from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from evalforge.config import get_settings
from evalforge.database import SessionLocal, get_db
from evalforge.models import (
    AgentConfiguration,
    Benchmark,
    BenchmarkStatus,
    EvaluationRun,
    Evaluator,
    Task,
    TaskRun,
    Workspace,
)
from evalforge.schemas import (
    AgentCreate,
    BenchmarkCreate,
    BenchmarkRead,
    FailureUpdate,
    RunCreate,
    RunRead,
    TaskCreate,
)
from evalforge.services.runs import execute_run

router = APIRouter(prefix="/api/v1")


async def _run_job(run_id: str) -> None:
    with SessionLocal() as session:
        execute_run(session, run_id)


def _workspace(session: Session) -> Workspace:
    workspace = session.scalar(select(Workspace).order_by(Workspace.created_at))
    if workspace is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No workspace is configured")
    return workspace


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dashboard")
async def dashboard(session: Session = Depends(get_db)) -> dict:
    runs = session.scalars(select(EvaluationRun).order_by(desc(EvaluationRun.created_at))).all()
    benchmarks = (
        session.scalar(
            select(func.count(Benchmark.id)).where(Benchmark.status == BenchmarkStatus.ACTIVE)
        )
        or 0
    )
    completed = [run for run in runs if run.status.value == "Completed"]
    return {
        "metrics": {
            "total_runs": len(runs),
            "average_pass_rate": sum(run.pass_at_k for run in completed) / len(completed)
            if completed
            else 0,
            "evaluated_tasks": sum(run.completed_tasks for run in runs),
            "active_benchmarks": benchmarks,
        },
        "recent_runs": [_run_summary(run) for run in runs[:6]],
    }


@router.get("/benchmarks")
async def list_benchmarks(
    search: str | None = None,
    session: Session = Depends(get_db),
) -> list[dict]:
    statement = (
        select(Benchmark)
        .options(selectinload(Benchmark.tasks), selectinload(Benchmark.runs))
        .order_by(Benchmark.name)
    )
    if search:
        statement = statement.where(Benchmark.name.ilike(f"%{search}%"))
    benchmarks = session.scalars(statement).all()
    return [
        {
            **BenchmarkRead.model_validate(item).model_dump(mode="json"),
            "task_count": len(item.tasks),
            "run_count": len(item.runs),
            "latest_pass_rate": max(item.runs, key=lambda run: run.created_at).pass_at_k
            if item.runs
            else None,
        }
        for item in benchmarks
    ]


@router.post("/benchmarks", status_code=status.HTTP_201_CREATED)
async def create_benchmark(
    payload: BenchmarkCreate, session: Session = Depends(get_db)
) -> BenchmarkRead:
    if session.scalar(select(Benchmark).where(Benchmark.slug == payload.slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Benchmark slug already exists")
    benchmark = Benchmark(workspace_id=_workspace(session).id, **payload.model_dump())
    session.add(benchmark)
    session.commit()
    session.refresh(benchmark)
    return BenchmarkRead.model_validate(benchmark)


@router.get("/benchmarks/{benchmark_id}")
async def get_benchmark(benchmark_id: str, session: Session = Depends(get_db)) -> dict:
    benchmark = session.scalar(
        select(Benchmark)
        .where(Benchmark.id == benchmark_id)
        .options(
            selectinload(Benchmark.tasks).selectinload(Task.evaluators),
            selectinload(Benchmark.runs),
        )
    )
    if benchmark is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benchmark not found")
    return {
        **BenchmarkRead.model_validate(benchmark).model_dump(mode="json"),
        "tasks": [_task_payload(task) for task in benchmark.tasks],
        "runs": [
            _run_summary(run)
            for run in sorted(benchmark.runs, key=lambda item: item.created_at, reverse=True)
        ],
    }


@router.post("/benchmarks/{benchmark_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    benchmark_id: str, payload: TaskCreate, session: Session = Depends(get_db)
) -> dict:
    if session.get(Benchmark, benchmark_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benchmark not found")
    if session.scalar(
        select(Task).where(Task.benchmark_id == benchmark_id, Task.slug == payload.slug)
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Task slug already exists in this benchmark")
    values = payload.model_dump(exclude={"evaluators", "metadata"})
    task = Task(benchmark_id=benchmark_id, task_metadata=payload.metadata, **values)
    session.add(task)
    session.flush()
    for evaluator in payload.evaluators:
        session.add(Evaluator(task_id=task.id, **evaluator.model_dump()))
    session.commit()
    session.refresh(task, attribute_names=["evaluators"])
    return _task_payload(task)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str, payload: TaskCreate, session: Session = Depends(get_db)
) -> dict:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    if session.scalar(
        select(Task).where(
            Task.benchmark_id == task.benchmark_id,
            Task.slug == payload.slug,
            Task.id != task.id,
        )
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Task slug already exists in this benchmark")
    for key, value in payload.model_dump(exclude={"evaluators", "metadata"}).items():
        setattr(task, key, value)
    task.task_metadata = payload.metadata
    session.query(Evaluator).filter(Evaluator.task_id == task.id).delete()
    session.flush()
    for evaluator in payload.evaluators:
        session.add(Evaluator(task_id=task.id, **evaluator.model_dump()))
    session.commit()
    session.refresh(task, attribute_names=["evaluators"])
    return _task_payload(task)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, session: Session = Depends(get_db)) -> dict:
    task = session.scalar(
        select(Task).where(Task.id == task_id).options(selectinload(Task.evaluators))
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return _task_payload(task)


@router.get("/agents")
async def list_agents(session: Session = Depends(get_db)) -> list[dict]:
    agents = session.scalars(select(AgentConfiguration).order_by(AgentConfiguration.name)).all()
    return [_agent_payload(agent) for agent in agents]


@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, session: Session = Depends(get_db)) -> dict:
    if payload.provider.casefold() != "mock":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "V1 demo mode currently supports the Mock provider",
        )
    agent = AgentConfiguration(workspace_id=_workspace(session).id, **payload.model_dump())
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return _agent_payload(agent)


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str, payload: AgentCreate, session: Session = Depends(get_db)
) -> dict:
    agent = session.get(AgentConfiguration, agent_id)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent configuration not found")
    if payload.provider.casefold() != "mock":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "V1 demo mode currently supports the Mock provider",
        )
    for key, value in payload.model_dump().items():
        setattr(agent, key, value)
    session.commit()
    session.refresh(agent)
    return _agent_payload(agent)


@router.get("/runs")
async def list_runs(session: Session = Depends(get_db)) -> list[dict]:
    runs = session.scalars(
        select(EvaluationRun)
        .options(
            selectinload(EvaluationRun.benchmark), selectinload(EvaluationRun.agent_configuration)
        )
        .order_by(desc(EvaluationRun.created_at))
    ).all()
    return [_run_summary(run, names=True) for run in runs]


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
async def start_run(
    payload: RunCreate, background: BackgroundTasks, session: Session = Depends(get_db)
) -> RunRead:
    benchmark = session.scalar(
        select(Benchmark)
        .where(Benchmark.id == payload.benchmark_id)
        .options(selectinload(Benchmark.tasks))
    )
    agent = session.get(AgentConfiguration, payload.agent_configuration_id)
    if benchmark is None or agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benchmark or agent configuration not found")
    if benchmark.status != BenchmarkStatus.ACTIVE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only active benchmarks can be evaluated")
    if not benchmark.tasks:
        raise HTTPException(status.HTTP_409_CONFLICT, "Add at least one task before starting a run")
    if agent.workspace_id != benchmark.workspace_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Benchmark and agent must share a workspace")
    run = EvaluationRun(
        benchmark_id=benchmark.id,
        agent_configuration_id=agent.id,
        attempts=payload.attempts,
        total_tasks=len(benchmark.tasks) * payload.attempts,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    if get_settings().inline_jobs:
        background.add_task(_run_job, run.id)
    else:
        from evalforge.worker import execute_evaluation

        execute_evaluation.send(run.id)
    return RunRead.model_validate(run)


@router.get("/runs/compare")
async def compare_runs(ids: list[str] = Query(), session: Session = Depends(get_db)) -> list[dict]:
    if len(ids) < 2:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Select at least two runs")
    runs = session.scalars(
        select(EvaluationRun)
        .where(EvaluationRun.id.in_(ids))
        .options(
            selectinload(EvaluationRun.benchmark),
            selectinload(EvaluationRun.agent_configuration),
        )
    ).all()
    by_id = {run.id: run for run in runs}
    return [_run_summary(by_id[run_id], names=True) for run_id in ids if run_id in by_id]


@router.get("/runs/{run_id}")
async def get_run(run_id: str, session: Session = Depends(get_db)) -> dict:
    run = session.scalar(
        select(EvaluationRun)
        .where(EvaluationRun.id == run_id)
        .options(
            selectinload(EvaluationRun.benchmark),
            selectinload(EvaluationRun.agent_configuration),
            selectinload(EvaluationRun.task_runs).selectinload(TaskRun.task),
            selectinload(EvaluationRun.task_runs).selectinload(TaskRun.events),
            selectinload(EvaluationRun.task_runs).selectinload(TaskRun.results),
        )
    )
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found")
    return {
        **_run_summary(run, names=True),
        "task_runs": [
            {
                "id": item.id,
                "task_id": item.task_id,
                "task_name": item.task.name,
                "status": item.status.value,
                "attempt_number": item.attempt_number,
                "input": item.input,
                "output": item.output,
                "score": item.score,
                "passed": item.passed,
                "failure_category": item.failure_category.value if item.failure_category else None,
                "duration_ms": item.duration_ms,
                "input_tokens": item.input_tokens,
                "output_tokens": item.output_tokens,
                "events": [
                    {
                        "id": event.id,
                        "type": event.event_type,
                        "sequence": event.sequence,
                        "payload": event.payload,
                        "timestamp": event.timestamp,
                    }
                    for event in sorted(item.events, key=lambda event: event.sequence)
                ],
                "results": [
                    {
                        "id": result.id,
                        "score": result.score,
                        "passed": result.passed,
                        "reason": result.reason,
                        "metadata": result.result_metadata,
                    }
                    for result in item.results
                ],
            }
            for item in sorted(
                run.task_runs, key=lambda value: (value.task.name, value.attempt_number)
            )
        ],
    }


@router.patch("/task-runs/{task_run_id}/failure")
async def classify_failure(
    task_run_id: str, payload: FailureUpdate, session: Session = Depends(get_db)
) -> dict:
    task_run = session.get(TaskRun, task_run_id)
    if task_run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task run not found")
    if task_run.passed:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Passing task runs cannot be classified as failures"
        )
    task_run.failure_category = payload.failure_category
    session.commit()
    return {"id": task_run.id, "failure_category": task_run.failure_category.value}


def _task_payload(task: Task) -> dict:
    return {
        "id": task.id,
        "benchmark_id": task.benchmark_id,
        "name": task.name,
        "slug": task.slug,
        "description": task.description,
        "instruction": task.instruction,
        "input": task.input,
        "metadata": task.task_metadata,
        "timeout_seconds": task.timeout_seconds,
        "difficulty": task.difficulty.value,
        "evaluators": [
            {
                "id": item.id,
                "type": item.type,
                "name": item.name,
                "configuration": item.configuration,
                "weight": item.weight,
            }
            for item in task.evaluators
        ],
    }


def _agent_payload(agent: AgentConfiguration) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "provider": agent.provider,
        "model": agent.model,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "system_prompt": agent.system_prompt,
        "configuration": agent.configuration,
    }


def _run_summary(run: EvaluationRun, names: bool = False) -> dict:
    payload = RunRead.model_validate(run).model_dump(mode="json")
    if names:
        payload.update(benchmark_name=run.benchmark.name, agent_name=run.agent_configuration.name)
    return payload
