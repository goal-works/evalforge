from sqlalchemy import func, select
from sqlalchemy.orm import Session

from evalforge.models import (
    AgentConfiguration,
    Benchmark,
    BenchmarkStatus,
    Difficulty,
    EvaluationRun,
    Evaluator,
    Task,
    Workspace,
)
from evalforge.services.runs import execute_run

REASONING_TASKS = [
    (
        "Priority queue",
        "priority-queue",
        "Return the next ticket ID by severity, then age.",
        {"tickets": ["T-104", "T-108", "T-111"]},
        "T-108",
        Difficulty.EASY,
    ),
    (
        "Incident summary",
        "incident-summary",
        "Summarize the incident and include the resolution owner.",
        {"incident": "Cache saturation delayed requests; Platform restored capacity."},
        "Owner: Platform",
        Difficulty.MEDIUM,
    ),
    (
        "Policy decision",
        "policy-decision",
        "Choose approve or escalate and give a concise rationale.",
        {"risk": "high", "evidence": "incomplete"},
        "escalate",
        Difficulty.MEDIUM,
    ),
    (
        "Dependency order",
        "dependency-order",
        "Return a valid deployment order for api, database, and web.",
        {"dependencies": {"api": ["database"], "web": ["api"]}},
        "database, api, web",
        Difficulty.EASY,
    ),
    (
        "Constraint check",
        "constraint-check",
        "Identify whether the proposal violates the stated budget.",
        {"budget": 800, "proposal": 950},
        "over budget",
        Difficulty.EASY,
    ),
    (
        "Support routing",
        "support-routing",
        "Route this issue to billing, product, or security.",
        {"message": "An unknown card was charged twice."},
        "billing",
        Difficulty.MEDIUM,
    ),
    (
        "Release verdict",
        "release-verdict",
        "Return a release verdict that mentions tests and rollback readiness.",
        {"tests": "passing", "rollback": "verified"},
        "release",
        Difficulty.HARD,
    ),
    (
        "Evidence review",
        "evidence-review",
        "Explain why the claim is not yet supported and name the missing evidence.",
        {"claim": "latency improved", "measurement": None},
        "measurement",
        Difficulty.HARD,
    ),
]

JSON_TASKS = [
    (
        "Contact record",
        "contact-record",
        ["name", "email"],
        {"name": "Demo User", "email": "demo@example.test"},
    ),
    ("Issue label", "issue-label", ["label", "confidence"], {"label": "bug", "confidence": 0.94}),
    (
        "Action plan",
        "action-plan",
        ["status", "steps"],
        {"status": "ready", "steps": ["verify", "deploy"]},
    ),
    ("Risk score", "risk-score", ["risk", "score"], {"risk": "medium", "score": 0.55}),
    ("Tool result", "tool-result", ["tool", "success"], {"tool": "lookup", "success": True}),
    (
        "Review outcome",
        "review-outcome",
        ["decision", "reasons"],
        {"decision": "revise", "reasons": ["missing evidence"]},
    ),
    ("Run summary", "run-summary", ["passed", "failed"], {"passed": 7, "failed": 1}),
]


def seed_demo_data(session: Session) -> None:
    if session.scalar(select(func.count(Workspace.id))):
        return

    workspace = Workspace(
        name="EvalForge Demo",
        slug="evalforge-demo",
        description="Deterministic local demonstration workspace.",
    )
    session.add(workspace)
    session.flush()
    reasoning = Benchmark(
        workspace_id=workspace.id,
        name="Operational Reasoning",
        slug="operational-reasoning",
        description="Concise decision-making tasks grounded in supplied operational evidence.",
        version="1.2.0",
        status=BenchmarkStatus.ACTIVE,
        difficulty=Difficulty.MEDIUM,
        tags=["reasoning", "operations"],
    )
    structured = Benchmark(
        workspace_id=workspace.id,
        name="Reliable Structured Output",
        slug="reliable-structured-output",
        description="JSON response-format and schema adherence checks.",
        version="1.0.0",
        status=BenchmarkStatus.ACTIVE,
        difficulty=Difficulty.MEDIUM,
        tags=["json", "reliability"],
    )
    session.add_all([reasoning, structured])
    session.flush()

    for index, (name, slug, instruction, input_value, expected, difficulty) in enumerate(
        REASONING_TASKS
    ):
        success_output = (
            expected
            if index < 6
            else f"{expected}; tests verified; rollback ready; measurement required"
        )
        task = Task(
            benchmark_id=reasoning.id,
            name=name,
            slug=slug,
            description="Deterministic decision task.",
            instruction=instruction,
            input=input_value,
            task_metadata={
                "mock_success_output": success_output,
                "mock_failure_output": "insufficient context",
            },
            difficulty=difficulty,
        )
        session.add(task)
        session.flush()
        evaluator_type = "exact_match" if index in {0, 3} else "contains"
        config = (
            {"expected": expected, "case_sensitive": False}
            if evaluator_type == "exact_match"
            else {"value": expected}
        )
        session.add(
            Evaluator(
                task_id=task.id, type=evaluator_type, name="Required answer", configuration=config
            )
        )

    for name, slug, required, output in JSON_TASKS:
        task = Task(
            benchmark_id=structured.id,
            name=name,
            slug=slug,
            description="Structured response contract.",
            instruction="Return only a JSON object matching the requested fields.",
            input={"required_fields": required},
            task_metadata={"mock_success_output": output, "mock_failure_output": "not-json"},
            difficulty=Difficulty.MEDIUM,
        )
        session.add(task)
        session.flush()
        properties = {
            key: {
                "type": "number"
                if key in {"confidence", "score", "passed", "failed"}
                else "array"
                if key in {"steps", "reasons"}
                else "boolean"
                if key == "success"
                else "string"
            }
            for key in required
        }
        session.add(
            Evaluator(
                task_id=task.id,
                type="json_schema",
                name="Response schema",
                configuration={
                    "schema": {"type": "object", "required": required, "properties": properties}
                },
            )
        )

    agents = [
        AgentConfiguration(
            workspace_id=workspace.id,
            name="Forge Strong",
            provider="Mock",
            model="mock-strong-v1",
            configuration={"quality": 0.92},
        ),
        AgentConfiguration(
            workspace_id=workspace.id,
            name="Forge Balanced",
            provider="Mock",
            model="mock-balanced-v1",
            configuration={"quality": 0.72},
        ),
        AgentConfiguration(
            workspace_id=workspace.id,
            name="Forge Fast",
            provider="Mock",
            model="mock-fast-v1",
            configuration={"quality": 0.48},
        ),
    ]
    session.add_all(agents)
    session.commit()

    for benchmark, agent in [
        (reasoning, agents[0]),
        (reasoning, agents[1]),
        (structured, agents[0]),
        (structured, agents[2]),
    ]:
        run = EvaluationRun(benchmark_id=benchmark.id, agent_configuration_id=agent.id, attempts=1)
        session.add(run)
        session.commit()
        execute_run(session, run.id)
