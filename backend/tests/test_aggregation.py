import pytest
from evalforge.core.aggregation import AttemptResult, aggregate_run, calculate_pass_at_k

RESULTS = [
    AttemptResult("task-a", 1, False, 0.2, tokens=10, duration_ms=100),
    AttemptResult("task-a", 2, True, 1.0, tokens=12, duration_ms=120),
    AttemptResult("task-b", 1, False, 0.0, tokens=8, duration_ms=80),
    AttemptResult("task-b", 2, False, 0.4, tokens=9, duration_ms=90),
]


def test_pass_at_k_uses_first_k_attempts_per_task() -> None:
    assert calculate_pass_at_k(RESULTS, 1) == 0
    assert calculate_pass_at_k(RESULTS, 2) == 0.5


def test_pass_at_k_rejects_invalid_k() -> None:
    with pytest.raises(ValueError):
        calculate_pass_at_k(RESULTS, 0)


def test_run_aggregation_counts_executions_and_totals() -> None:
    aggregate = aggregate_run(RESULTS, 2)
    assert aggregate.executions == 4
    assert aggregate.passed_executions == 1
    assert aggregate.mean_score == pytest.approx(0.4)
    assert aggregate.total_tokens == 39
    assert aggregate.duration_ms == 390
