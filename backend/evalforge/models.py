import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evalforge.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class BenchmarkStatus(StrEnum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    ARCHIVED = "Archived"


class Difficulty(StrEnum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"


class RunStatus(StrEnum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class FailureCategory(StrEnum):
    REASONING = "Reasoning"
    INSTRUCTION_FOLLOWING = "Instruction Following"
    TOOL_USAGE = "Tool Usage"
    INVALID_OUTPUT = "Invalid Output"
    INCOMPLETE_SOLUTION = "Incomplete Solution"
    HALLUCINATION = "Hallucination"
    TIMEOUT = "Timeout"
    ENVIRONMENT = "Environment"
    EVALUATOR_ERROR = "Evaluator Error"
    UNKNOWN = "Unknown"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    benchmarks: Mapped[list["Benchmark"]] = relationship(back_populates="workspace")
    agents: Mapped[list["AgentConfiguration"]] = relationship(back_populates="workspace")


class Benchmark(TimestampMixin, Base):
    __tablename__ = "benchmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    status: Mapped[BenchmarkStatus] = mapped_column(
        Enum(BenchmarkStatus), default=BenchmarkStatus.DRAFT
    )
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.MEDIUM)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    workspace: Mapped[Workspace] = relationship(back_populates="benchmarks")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="benchmark", cascade="all, delete-orphan"
    )
    runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="benchmark")


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("benchmark_id", "slug", name="uq_task_benchmark_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    benchmark_id: Mapped[str] = mapped_column(ForeignKey("benchmarks.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    instruction: Mapped[str] = mapped_column(Text)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    task_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.MEDIUM)

    benchmark: Mapped[Benchmark] = relationship(back_populates="tasks")
    evaluators: Mapped[list["Evaluator"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    task_runs: Mapped[list["TaskRun"]] = relationship(back_populates="task")


class AgentConfiguration(TimestampMixin, Base):
    __tablename__ = "agent_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(60), default="Mock")
    model: Mapped[str] = mapped_column(String(120))
    temperature: Mapped[float] = mapped_column(Float, default=0)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024)
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    workspace: Mapped[Workspace] = relationship(back_populates="agents")
    runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="agent_configuration")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    benchmark_id: Mapped[str] = mapped_column(ForeignKey("benchmarks.id"), index=True)
    agent_configuration_id: Mapped[str] = mapped_column(
        ForeignKey("agent_configurations.id"), index=True
    )
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.QUEUED, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    passed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    mean_score: Mapped[float] = mapped_column(Float, default=0)
    pass_at_k: Mapped[float] = mapped_column(Float, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    benchmark: Mapped[Benchmark] = relationship(back_populates="runs")
    agent_configuration: Mapped[AgentConfiguration] = relationship(back_populates="runs")
    task_runs: Mapped[list["TaskRun"]] = relationship(
        back_populates="evaluation_run", cascade="all, delete-orphan"
    )


class TaskRun(Base):
    __tablename__ = "task_runs"
    __table_args__ = (
        UniqueConstraint(
            "evaluation_run_id",
            "task_id",
            "attempt_number",
            name="uq_task_run_attempt",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    evaluation_run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.QUEUED)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output: Mapped[Any | None] = mapped_column(JSON)
    score: Mapped[float] = mapped_column(Float, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_category: Mapped[FailureCategory | None] = mapped_column(Enum(FailureCategory))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))

    evaluation_run: Mapped[EvaluationRun] = relationship(back_populates="task_runs")
    task: Mapped[Task] = relationship(back_populates="task_runs")
    events: Mapped[list["ExecutionEvent"]] = relationship(
        back_populates="task_run", cascade="all, delete-orphan"
    )
    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="task_run", cascade="all, delete-orphan"
    )


class ExecutionEvent(Base):
    __tablename__ = "execution_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    sequence: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    task_run: Mapped[TaskRun] = relationship(back_populates="events")


class Evaluator(TimestampMixin, Base):
    __tablename__ = "evaluators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    weight: Mapped[float] = mapped_column(Float, default=1)

    task: Mapped[Task] = relationship(back_populates="evaluators")
    results: Mapped[list["EvaluationResult"]] = relationship(back_populates="evaluator")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id"), index=True)
    evaluator_id: Mapped[str] = mapped_column(ForeignKey("evaluators.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str] = mapped_column(Text)
    result_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    task_run: Mapped[TaskRun] = relationship(back_populates="results")
    evaluator: Mapped[Evaluator] = relationship(back_populates="results")
