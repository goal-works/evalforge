from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class AttemptResult:
    task_id: str
    attempt_number: int
    passed: bool
    score: float
    tokens: int = 0
    cost: float = 0
    duration_ms: int = 0


@dataclass(frozen=True)
class RunAggregate:
    executions: int
    passed_executions: int
    failed_executions: int
    mean_score: float
    pass_at_k: float
    total_tokens: int
    estimated_cost: float
    duration_ms: int


def calculate_pass_at_k(results: Iterable[AttemptResult], k: int) -> float:
    if k < 1:
        raise ValueError("k must be at least 1")
    by_task: dict[str, list[AttemptResult]] = defaultdict(list)
    for result in results:
        by_task[result.task_id].append(result)
    if not by_task:
        return 0.0
    succeeded = sum(
        any(item.passed for item in sorted(attempts, key=lambda item: item.attempt_number)[:k])
        for attempts in by_task.values()
    )
    return succeeded / len(by_task)


def aggregate_run(results: Iterable[AttemptResult], k: int) -> RunAggregate:
    items = list(results)
    executions = len(items)
    passed = sum(item.passed for item in items)
    return RunAggregate(
        executions=executions,
        passed_executions=passed,
        failed_executions=executions - passed,
        mean_score=sum(item.score for item in items) / executions if executions else 0.0,
        pass_at_k=calculate_pass_at_k(items, k),
        total_tokens=sum(item.tokens for item in items),
        estimated_cost=sum(item.cost for item in items),
        duration_ms=sum(item.duration_ms for item in items),
    )
