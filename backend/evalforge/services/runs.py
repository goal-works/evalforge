from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from evalforge.core.aggregation import AttemptResult, aggregate_run
from evalforge.core.evaluators import evaluate
from evalforge.models import (
    Benchmark,
    EvaluationResult,
    EvaluationRun,
    ExecutionEvent,
    FailureCategory,
    RunStatus,
    TaskRun,
    now,
)
from evalforge.services.agents import get_adapter


def execute_run(session: Session, run_id: str) -> EvaluationRun:
    statement = (
        select(EvaluationRun)
        .where(EvaluationRun.id == run_id)
        .options(
            selectinload(EvaluationRun.agent_configuration),
            selectinload(EvaluationRun.benchmark).selectinload(Benchmark.tasks),
            selectinload(EvaluationRun.task_runs),
        )
    )
    run = session.scalar(statement)
    if run is None:
        raise LookupError(f"Run {run_id} was not found")
    if run.status not in {RunStatus.QUEUED, RunStatus.FAILED}:
        return run

    previous_status = run.status
    claimed_at = now()
    claim = session.execute(
        update(EvaluationRun)
        .where(EvaluationRun.id == run.id, EvaluationRun.status == previous_status)
        .values(status=RunStatus.RUNNING, started_at=claimed_at, completed_at=None)
    )
    session.commit()
    if claim.rowcount != 1:
        session.refresh(run)
        return run

    session.refresh(run)
    if previous_status == RunStatus.FAILED:
        run.task_runs.clear()
        run.completed_tasks = 0
        run.passed_tasks = 0
        run.failed_tasks = 0
        run.mean_score = 0
        run.pass_at_k = 0
        run.total_tokens = 0
        run.estimated_cost = Decimal("0")
        run.duration_ms = 0
        session.commit()

    try:
        adapter = get_adapter(run.agent_configuration.provider)
        tasks = list(run.benchmark.tasks)
        run.total_tasks = len(tasks) * run.attempts
        session.commit()
        for task in tasks:
            session.refresh(task, attribute_names=["evaluators"])
            for attempt in range(1, run.attempts + 1):
                task_run = TaskRun(
                    evaluation_run_id=run.id,
                    task_id=task.id,
                    status=RunStatus.RUNNING,
                    attempt_number=attempt,
                    input=task.input,
                    started_at=now(),
                )
                session.add(task_run)
                session.flush()
                execution = adapter.execute(run.agent_configuration, task, attempt)
                for sequence, (event_type, payload) in enumerate(execution.events, start=1):
                    session.add(
                        ExecutionEvent(
                            task_run_id=task_run.id,
                            event_type=event_type,
                            sequence=sequence,
                            payload=payload,
                        )
                    )

                weighted_score = 0.0
                total_weight = 0.0
                all_passed = True
                for evaluator in task.evaluators:
                    outcome = evaluate(evaluator.type, execution.output, evaluator.configuration)
                    weighted_score += outcome.score * evaluator.weight
                    total_weight += evaluator.weight
                    all_passed = all_passed and outcome.passed
                    session.add(
                        EvaluationResult(
                            task_run_id=task_run.id,
                            evaluator_id=evaluator.id,
                            score=outcome.score,
                            passed=outcome.passed,
                            reason=outcome.reason,
                            result_metadata=outcome.metadata,
                        )
                    )
                task_run.output = execution.output
                task_run.score = weighted_score / total_weight if total_weight else 0.0
                task_run.passed = bool(task.evaluators) and all_passed
                task_run.failure_category = None if task_run.passed else FailureCategory.UNKNOWN
                task_run.status = RunStatus.COMPLETED
                task_run.completed_at = now()
                task_run.duration_ms = execution.duration_ms
                task_run.input_tokens = execution.input_tokens
                task_run.output_tokens = execution.output_tokens
                task_run.estimated_cost = Decimal(str(execution.estimated_cost))
                run.completed_tasks += 1
                session.commit()

        refresh_aggregate(session, run)
        run.status = RunStatus.COMPLETED
        run.completed_at = now()
        session.commit()
    except Exception:
        session.rollback()
        run = session.get(EvaluationRun, run_id)
        if run is None:
            raise
        run.status = RunStatus.FAILED
        run.completed_at = now()
        session.commit()
        raise
    return run


def refresh_aggregate(session: Session, run: EvaluationRun) -> None:
    task_runs = session.scalars(select(TaskRun).where(TaskRun.evaluation_run_id == run.id)).all()
    aggregate = aggregate_run(
        (
            AttemptResult(
                task_id=item.task_id,
                attempt_number=item.attempt_number,
                passed=item.passed,
                score=item.score,
                tokens=item.input_tokens + item.output_tokens,
                cost=float(item.estimated_cost),
                duration_ms=item.duration_ms,
            )
            for item in task_runs
        ),
        run.attempts,
    )
    run.completed_tasks = aggregate.executions
    run.passed_tasks = aggregate.passed_executions
    run.failed_tasks = aggregate.failed_executions
    run.mean_score = aggregate.mean_score
    run.pass_at_k = aggregate.pass_at_k
    run.total_tokens = aggregate.total_tokens
    run.estimated_cost = Decimal(str(aggregate.estimated_cost))
    run.duration_ms = aggregate.duration_ms
