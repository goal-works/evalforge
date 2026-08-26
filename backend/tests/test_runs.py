from evalforge.database import SessionLocal
from evalforge.models import EvaluationRun, RunStatus
from evalforge.services.runs import execute_run
from sqlalchemy import select
from sqlalchemy.orm import selectinload


def test_completed_run_delivery_is_idempotent(client) -> None:
    run_id = client.get("/api/v1/runs").json()[0]["id"]
    with SessionLocal() as session:
        run = session.scalar(
            select(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .options(selectinload(EvaluationRun.task_runs))
        )
        assert run is not None
        execution_count = len(run.task_runs)
        execute_run(session, run.id)
        session.refresh(run, attribute_names=["task_runs"])
        assert len(run.task_runs) == execution_count


def test_failed_run_retry_replaces_partial_attempts(client) -> None:
    run_id = client.get("/api/v1/runs").json()[0]["id"]
    with SessionLocal() as session:
        run = session.scalar(
            select(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .options(selectinload(EvaluationRun.task_runs))
        )
        assert run is not None
        expected_executions = run.total_tasks
        run.status = RunStatus.FAILED
        session.commit()

        execute_run(session, run.id)
        session.refresh(run, attribute_names=["task_runs"])
        assert run.status == RunStatus.COMPLETED
        assert len(run.task_runs) == expected_executions
