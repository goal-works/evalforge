# Benchmark format

A benchmark is a versioned collection of tasks. Each task contains a stable slug, instruction, JSON input, timeout, difficulty, optional metadata, and at least one evaluator.

```json
{
  "name": "Health response",
  "slug": "health-response",
  "instruction": "Return ok.",
  "input": {},
  "metadata": {
    "mock_success_output": "ok",
    "mock_failure_output": "error"
  },
  "timeout_seconds": 30,
  "difficulty": "Easy",
  "evaluators": [
    {
      "type": "exact_match",
      "name": "Expected output",
      "configuration": { "expected": "ok" },
      "weight": 1
    }
  ]
}
```

The `mock_*` metadata keys are demo fixtures, not a general answer-export format. Real provider adapters receive task instruction and input but should not receive evaluator configuration or expected values.
