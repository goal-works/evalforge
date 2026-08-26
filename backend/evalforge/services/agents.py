import hashlib
import json
from dataclasses import dataclass
from typing import Any

from evalforge.models import AgentConfiguration, Task


@dataclass(frozen=True)
class AgentExecution:
    output: Any
    events: list[tuple[str, dict[str, Any]]]
    input_tokens: int
    output_tokens: int
    duration_ms: int
    estimated_cost: float


class MockAgentAdapter:
    """Deterministic adapter that makes the complete product usable without API keys."""

    def execute(self, agent: AgentConfiguration, task: Task, attempt_number: int) -> AgentExecution:
        quality = float(agent.configuration.get("quality", 0.75))
        seed = f"{agent.model}:{task.slug}:{attempt_number}".encode()
        roll = int(hashlib.sha256(seed).hexdigest()[:8], 16) / 0xFFFFFFFF
        succeeded = roll <= quality
        output = (
            task.task_metadata.get("mock_success_output")
            if succeeded
            else task.task_metadata.get("mock_failure_output")
        )
        if output is None:
            output = (
                {"status": "complete", "summary": task.name} if succeeded else {"status": "partial"}
            )
        input_tokens = max(12, len(task.instruction.split()) + len(json.dumps(task.input).split()))
        output_tokens = max(8, len(json.dumps(output).split()))
        duration_ms = 180 + int(roll * 820)
        events = [
            (
                "model_request",
                {"provider": "Mock", "model": agent.model, "attempt": attempt_number},
            ),
            ("log", {"message": "Deterministic mock execution completed."}),
            ("model_response", {"tokens": output_tokens, "duration_ms": duration_ms}),
            ("final_output", {"output": output}),
        ]
        return AgentExecution(output, events, input_tokens, output_tokens, duration_ms, 0.0)


def get_adapter(provider: str) -> MockAgentAdapter:
    if provider.casefold() != "mock":
        raise ValueError(f"Provider {provider!r} is not available in demo mode.")
    return MockAgentAdapter()
