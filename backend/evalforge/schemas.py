from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from evalforge.models import BenchmarkStatus, Difficulty, FailureCategory, RunStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EvaluatorInput(BaseModel):
    type: Literal["exact_match", "contains", "json_schema", "deterministic_judge"]
    name: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1, gt=0)

    @model_validator(mode="after")
    def validate_configuration(self):
        if self.type == "exact_match" and "expected" not in self.configuration:
            raise ValueError("Exact Match requires an expected value")
        if self.type == "contains" and not str(self.configuration.get("value", "")).strip():
            raise ValueError("Contains requires a non-empty value")
        if self.type == "json_schema" and not isinstance(self.configuration.get("schema"), dict):
            raise ValueError("JSON Schema requires a schema object")
        if self.type == "deterministic_judge":
            criteria = self.configuration.get("criteria")
            threshold = self.configuration.get("threshold", 0.7)
            if not isinstance(criteria, list) or not criteria:
                raise ValueError("Deterministic Judge requires at least one criterion")
            if not 0 <= float(threshold) <= 1:
                raise ValueError("Deterministic Judge threshold must be between 0 and 1")
        return self


class BenchmarkCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = ""
    version: str = "1.0.0"
    status: BenchmarkStatus = BenchmarkStatus.DRAFT
    difficulty: Difficulty = Difficulty.MEDIUM
    tags: list[str] = Field(default_factory=list)


class BenchmarkRead(ORMModel):
    id: str
    name: str
    slug: str
    description: str
    version: str
    status: BenchmarkStatus
    difficulty: Difficulty
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = ""
    instruction: str = Field(min_length=3)
    input: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=3600)
    difficulty: Difficulty = Difficulty.MEDIUM
    evaluators: list[EvaluatorInput] = Field(min_length=1)


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    provider: str = "Mock"
    model: str = Field(min_length=2, max_length=120)
    temperature: float = Field(default=0, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1)
    system_prompt: str = ""
    configuration: dict[str, Any] = Field(default_factory=dict)

    @field_validator("configuration")
    @classmethod
    def validate_mock_quality(cls, configuration: dict[str, Any]) -> dict[str, Any]:
        if "quality" in configuration and not 0 <= float(configuration["quality"]) <= 1:
            raise ValueError("Mock quality must be between 0 and 1")
        return configuration


class RunCreate(BaseModel):
    benchmark_id: str
    agent_configuration_id: str
    attempts: int = Field(default=1, ge=1, le=5)


class FailureUpdate(BaseModel):
    failure_category: FailureCategory


class RunRead(ORMModel):
    id: str
    benchmark_id: str
    agent_configuration_id: str
    status: RunStatus
    attempts: int
    total_tasks: int
    completed_tasks: int
    passed_tasks: int
    failed_tasks: int
    mean_score: float
    pass_at_k: float
    total_tokens: int
    estimated_cost: float
    duration_ms: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
