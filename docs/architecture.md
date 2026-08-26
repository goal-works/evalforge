# Architecture

```text
Browser → Next.js web → FastAPI API → PostgreSQL
                         │
                         └→ Redis → Dramatiq worker
                                      │
                                      ├→ Agent adapter
                                      └→ Evaluator registry
```

The API owns validation and persisted state. Run creation is transactional: the run is written as `Queued` before a job is dispatched. A worker loads the benchmark and agent configuration, creates one task run per task and attempt, records ordered execution events, executes evaluators, persists individual results, and updates aggregates.

## State and idempotency

Workers atomically transition only `Queued` or `Failed` runs to `Running`. A duplicate delivery for a claimed, completed, or cancelled run returns without creating task runs. Retrying a failed run deletes its partial task attempts and resets aggregates before execution, while database uniqueness constraints prevent duplicate task/attempt records. The V1 worker remains single-process by default; higher-scale deployments should add database-specific row locking and worker lease recovery.

Local development defaults to inline background jobs so Redis is optional. Docker sets `EVALFORGE_INLINE_JOBS=false` and uses the same application service through Dramatiq.

## Adapter contract

An agent adapter returns output, ordered event tuples, token counts, duration, and estimated cost. V1 enables only the deterministic Mock adapter. Provider credentials and network calls are deliberately outside the initial trust boundary.

## Evaluator contract

Every evaluator returns a score from 0 to 1, a pass verdict, a human-readable reason, and structured metadata. Task-run score is the weighted evaluator mean; the task-run pass verdict requires every configured evaluator to pass.
