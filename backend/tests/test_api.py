def test_seeded_dashboard_and_benchmarks(client) -> None:
    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["metrics"]["total_runs"] == 4

    benchmarks = client.get("/api/v1/benchmarks")
    assert benchmarks.status_code == 200
    assert len(benchmarks.json()) == 2
    assert sum(item["task_count"] for item in benchmarks.json()) == 15

    client.post("/api/v1/benchmarks", json={"name": "Draft suite", "slug": "draft-suite"})
    assert client.get("/api/v1/dashboard").json()["metrics"]["active_benchmarks"] == 2


def test_create_benchmark_task_and_run_with_mock_agent(client) -> None:
    benchmark_response = client.post(
        "/api/v1/benchmarks",
        json={
            "name": "API Contract",
            "slug": "api-contract",
            "status": "Active",
            "difficulty": "Easy",
        },
    )
    assert benchmark_response.status_code == 201
    benchmark = benchmark_response.json()

    task_response = client.post(
        f"/api/v1/benchmarks/{benchmark['id']}/tasks",
        json={
            "name": "Health response",
            "slug": "health-response",
            "instruction": "Return ok.",
            "metadata": {"mock_success_output": "ok", "mock_failure_output": "error"},
            "evaluators": [
                {
                    "type": "exact_match",
                    "name": "Expected output",
                    "configuration": {"expected": "ok"},
                }
            ],
        },
    )
    assert task_response.status_code == 201

    agent = client.get("/api/v1/agents").json()[0]
    run_response = client.post(
        "/api/v1/runs",
        json={
            "benchmark_id": benchmark["id"],
            "agent_configuration_id": agent["id"],
            "attempts": 2,
        },
    )
    assert run_response.status_code == 202
    run = client.get(f"/api/v1/runs/{run_response.json()['id']}")
    assert run.status_code == 200
    assert run.json()["status"] == "Completed"
    assert len(run.json()["task_runs"]) == 2
    assert run.json()["pass_at_k"] in {0, 1}


def test_failure_classification_is_persisted(client) -> None:
    task_run = None
    for run in client.get("/api/v1/runs").json():
        detail = client.get(f"/api/v1/runs/{run['id']}").json()
        task_run = next((item for item in detail["task_runs"] if not item["passed"]), None)
        if task_run:
            break
    assert task_run is not None
    response = client.patch(
        f"/api/v1/task-runs/{task_run['id']}/failure",
        json={"failure_category": "Reasoning"},
    )
    assert response.status_code == 200
    assert response.json()["failure_category"] == "Reasoning"


def test_task_slugs_are_unique_within_a_benchmark(client) -> None:
    benchmark = client.get("/api/v1/benchmarks").json()[0]
    payload = {
        "name": "Duplicate check",
        "slug": "duplicate-check",
        "instruction": "Return ok.",
        "metadata": {"mock_success_output": "ok"},
        "evaluators": [
            {
                "type": "exact_match",
                "name": "Expected",
                "configuration": {"expected": "ok"},
            }
        ],
    }
    assert (
        client.post(f"/api/v1/benchmarks/{benchmark['id']}/tasks", json=payload).status_code == 201
    )
    assert (
        client.post(f"/api/v1/benchmarks/{benchmark['id']}/tasks", json=payload).status_code == 409
    )


def test_invalid_evaluator_configuration_is_rejected(client) -> None:
    benchmark = client.get("/api/v1/benchmarks").json()[0]
    response = client.post(
        f"/api/v1/benchmarks/{benchmark['id']}/tasks",
        json={
            "name": "Broken evaluator",
            "slug": "broken-evaluator",
            "instruction": "Return a value.",
            "evaluators": [
                {"type": "contains", "name": "Missing configuration", "configuration": {}}
            ],
        },
    )
    assert response.status_code == 422


def test_empty_or_draft_benchmarks_cannot_start(client) -> None:
    benchmark = client.post(
        "/api/v1/benchmarks",
        json={"name": "Empty active", "slug": "empty-active", "status": "Active"},
    ).json()
    agent = client.get("/api/v1/agents").json()[0]
    response = client.post(
        "/api/v1/runs",
        json={"benchmark_id": benchmark["id"], "agent_configuration_id": agent["id"]},
    )
    assert response.status_code == 409


def test_passing_task_run_cannot_receive_failure_category(client) -> None:
    for run in client.get("/api/v1/runs").json():
        detail = client.get(f"/api/v1/runs/{run['id']}").json()
        task_run = next((item for item in detail["task_runs"] if item["passed"]), None)
        if task_run:
            break
    assert task_run is not None
    response = client.patch(
        f"/api/v1/task-runs/{task_run['id']}/failure",
        json={"failure_category": "Reasoning"},
    )
    assert response.status_code == 409


def test_task_detail_and_agent_update(client) -> None:
    benchmark = client.get("/api/v1/benchmarks").json()[0]
    task = client.get(f"/api/v1/benchmarks/{benchmark['id']}").json()["tasks"][0]
    assert client.get(f"/api/v1/tasks/{task['id']}").json()["slug"] == task["slug"]

    agent = client.get("/api/v1/agents").json()[0]
    response = client.put(
        f"/api/v1/agents/{agent['id']}",
        json={
            "name": "Updated mock",
            "provider": "Mock",
            "model": "mock-updated-v1",
            "temperature": 0,
            "max_tokens": 512,
            "configuration": {"quality": 0.8},
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated mock"


def test_invalid_mock_quality_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Impossible mock",
            "model": "mock-impossible-v1",
            "configuration": {"quality": 1.5},
        },
    )
    assert response.status_code == 422


def test_run_comparison_preserves_selection_order_and_names(client) -> None:
    runs = client.get("/api/v1/runs").json()[:2]
    response = client.get(
        "/api/v1/runs/compare",
        params=[("ids", runs[1]["id"]), ("ids", runs[0]["id"])],
    )
    assert response.status_code == 200
    comparison = response.json()
    assert [item["id"] for item in comparison] == [runs[1]["id"], runs[0]["id"]]
    assert all(item["benchmark_name"] and item["agent_name"] for item in comparison)
