# Development and testing

## Native services

Run `uv sync --all-groups`, apply the schema with `uv run alembic upgrade head`, then start the API with `uv run uvicorn evalforge.main:app --reload --app-dir backend`. In `frontend`, run `npm install` and `npm run dev`. SQLite and inline execution are the defaults.

## Full stack

Copy `.env.example` to `.env` if custom values are needed, then run `docker compose up --build`. The web application is available on port 3000 and OpenAPI on port 8000.

## Validation

Backend: `uv run ruff check backend && uv run pytest`.

Migration drift: `uv run alembic check`.

Frontend: `cd frontend && npm run validate`.

Browser workflow and accessibility: `cd frontend && npm run test:e2e`.

The deterministic seed is inserted only when the workspace table is empty. Delete the local SQLite database or remove named Docker volumes only when an intentional clean reset is required.
