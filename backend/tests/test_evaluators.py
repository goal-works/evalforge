import pytest
from evalforge.core.evaluators import contains, deterministic_judge, exact_match, json_schema


def test_exact_match_can_ignore_case() -> None:
    outcome = exact_match("APPROVE", {"expected": "approve", "case_sensitive": False})
    assert outcome.passed
    assert outcome.score == 1


def test_contains_reports_missing_required_text() -> None:
    outcome = contains("route to product", {"value": "security"})
    assert not outcome.passed
    assert "not found" in outcome.reason


@pytest.mark.parametrize(
    ("output", "passed"),
    [
        ({"status": "ready", "count": 2}, True),
        ({"status": "ready"}, False),
        ("not-json", False),
    ],
)
def test_json_schema_required_fields_and_types(output, passed: bool) -> None:
    outcome = json_schema(
        output,
        {
            "schema": {
                "type": "object",
                "required": ["status", "count"],
                "properties": {"status": {"type": "string"}, "count": {"type": "integer"}},
            }
        },
    )
    assert outcome.passed is passed


def test_deterministic_judge_scores_criteria() -> None:
    outcome = deterministic_judge(
        "Tests are passing and rollback is ready.",
        {"criteria": ["tests", "rollback", "monitoring"], "threshold": 0.66},
    )
    assert outcome.passed
    assert outcome.score == pytest.approx(2 / 3)
