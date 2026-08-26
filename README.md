# EvalForge

EvalForge is open-source infrastructure for evaluating AI models and agents against reproducible benchmarks. V1 ships with deterministic mock agents, original demo tasks, persisted evaluator results, execution traces, failure classification, and pass@k aggregation, so the full workflow works without paid API keys.

## Current build status

The V1 implementation includes the backend domain model, evaluation engine, worker, REST API, Alembic schema migrations, deterministic demo seed, API-backed product screens, benchmark/task/agent editing workflows, multi-run comparison, Docker workflow, CI, backend tests, and browser E2E/accessibility coverage. Full Docker runtime validation remains environment-dependent.

## Local backend quick start

Prerequisites: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn evalforge.main:app --reload --app-dir backend
```

Then open `http://localhost:8000/docs`. On first startup, EvalForge creates a local SQLite database and seeds one demo workspace, two original benchmarks, 15 tasks, three deterministic mock agents, and historical evaluation runs.

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` for the product UI. For PostgreSQL, Redis, and the separate worker process, use `docker compose up --build` from the repository root.

Run validation with:

```bash
uv run ruff check backend
uv run pytest
```

## Evaluation lifecycle

1. A run is persisted as `Queued` with an immutable benchmark and agent selection.
2. The local development dispatcher or Redis-backed Dramatiq worker claims it and marks it `Running`.
3. Each task and attempt produces a task run, ordered execution events, token/latency data, and evaluator results.
4. Exact Match, Contains, JSON Schema, or Deterministic Judge evaluator contracts return a score, verdict, reason, and metadata.
5. Aggregation persists execution counts, mean score, token and cost totals, duration, and simplified pass@k.
6. The run reaches `Completed` or `Failed`; individual failures remain inspectable and manually classifiable.

The V1 pass@k definition is the percentage of tasks where at least one of the first `k` attempts passed.

## Repository layout

```text
backend/evalforge/   FastAPI application, SQLAlchemy model, engine, worker
backend/tests/       Evaluator, aggregation, API, and workflow tests
frontend/            Next.js application and Playwright browser tests
docs/                Architecture and operator documentation
```

## Demo data and privacy

All seeded benchmark tasks and agent configurations are original, deterministic fixtures created for this project. Names such as “Forge Strong” describe mock execution profiles; they do not represent real providers, people, customers, or measured third-party model performance.
