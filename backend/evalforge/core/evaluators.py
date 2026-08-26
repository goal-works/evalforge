import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvaluationOutcome:
    score: float
    passed: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def exact_match(output: Any, configuration: dict[str, Any]) -> EvaluationOutcome:
    expected = configuration.get("expected")
    case_sensitive = configuration.get("case_sensitive", True)
    actual_text = _as_text(output)
    expected_text = _as_text(expected)
    if not case_sensitive:
        actual_text, expected_text = actual_text.casefold(), expected_text.casefold()
    passed = actual_text == expected_text
    return EvaluationOutcome(
        score=1.0 if passed else 0.0,
        passed=passed,
        reason="Output matched the expected value."
        if passed
        else "Output did not exactly match the expected value.",
        metadata={"case_sensitive": case_sensitive},
    )


def contains(output: Any, configuration: dict[str, Any]) -> EvaluationOutcome:
    expected = str(configuration.get("value", ""))
    actual = _as_text(output)
    case_sensitive = configuration.get("case_sensitive", False)
    if not case_sensitive:
        expected, actual = expected.casefold(), actual.casefold()
    passed = bool(expected) and expected in actual
    return EvaluationOutcome(
        score=1.0 if passed else 0.0,
        passed=passed,
        reason="Output contained the required text."
        if passed
        else "Required text was not found in the output.",
        metadata={"case_sensitive": case_sensitive},
    )


def _matches_type(value: Any, expected_type: str) -> bool:
    checks = {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
        "null": lambda item: item is None,
    }
    return expected_type in checks and checks[expected_type](value)


def json_schema(output: Any, configuration: dict[str, Any]) -> EvaluationOutcome:
    try:
        value = json.loads(output) if isinstance(output, str) else output
    except json.JSONDecodeError:
        return EvaluationOutcome(0.0, False, "Output was not valid JSON.")

    schema = configuration.get("schema", {})
    expected_type = schema.get("type", "object")
    if not _matches_type(value, expected_type):
        return EvaluationOutcome(0.0, False, f"Expected JSON type {expected_type}.")

    missing = [
        key for key in schema.get("required", []) if not isinstance(value, dict) or key not in value
    ]
    if missing:
        return EvaluationOutcome(
            0.0, False, f"Missing required fields: {', '.join(missing)}.", {"missing": missing}
        )

    invalid = []
    if isinstance(value, dict):
        for key, rule in schema.get("properties", {}).items():
            if key in value and "type" in rule and not _matches_type(value[key], rule["type"]):
                invalid.append(key)
    if invalid:
        return EvaluationOutcome(
            0.0, False, f"Fields had invalid types: {', '.join(invalid)}.", {"invalid": invalid}
        )
    return EvaluationOutcome(1.0, True, "Output satisfied the configured JSON schema.")


def deterministic_judge(output: Any, configuration: dict[str, Any]) -> EvaluationOutcome:
    text = _as_text(output).casefold()
    criteria = [str(item).casefold() for item in configuration.get("criteria", [])]
    if not criteria:
        return EvaluationOutcome(0.0, False, "No deterministic judge criteria were configured.")
    hits = [criterion for criterion in criteria if criterion in text]
    score = len(hits) / len(criteria)
    threshold = float(configuration.get("threshold", 0.7))
    passed = score >= threshold
    return EvaluationOutcome(
        score=score,
        passed=passed,
        reason=f"Matched {len(hits)} of {len(criteria)} deterministic criteria.",
        metadata={"matched": hits, "threshold": threshold},
    )


EVALUATORS = {
    "exact_match": exact_match,
    "contains": contains,
    "json_schema": json_schema,
    "deterministic_judge": deterministic_judge,
}


def evaluate(evaluator_type: str, output: Any, configuration: dict[str, Any]) -> EvaluationOutcome:
    try:
        evaluator = EVALUATORS[evaluator_type]
    except KeyError as error:
        raise ValueError(f"Unsupported evaluator type: {evaluator_type}") from error
    return evaluator(output, configuration)
