# Deployment

## Local Development

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

SQLite is the default local database, so Docker is not required for a smoke test.

## Production Deployment

- Run FastAPI behind a reverse proxy or ingress controller.
- Run Celery workers separately from the API process.
- Scale workers independently based on queue depth.
- Persist PostgreSQL on managed storage such as NeonDB.
- Use Redis as a cache and broker only, not a durable source of truth.
- Use a sandboxed execution service for generated code and tests.

## Suggested Runtime Topology

- `api`: FastAPI stateless web pods.
- `worker`: Celery workers for generation, repair, and async tasks.
- `scheduler`: periodic jobs for scheduled workflow triggers.
- `postgres`: workflow state, plans, runs, and execution history.
- `redis`: broker and short-lived coordination.
- `frontend`: Next.js web UI.
- `sandbox`: isolated code runner for build and test jobs.

## Scaling Notes

- Scale horizontally when queue depth increases.
- Cap execution depth and retry count to avoid runaway graphs.
- Use idempotency keys for webhook ingestion.
- Use persisted checkpoints for resumable long-running workflows.
- Keep agent and tool outputs structured as JSON for deterministic replay.
- Route model calls dynamically to control cost and latency.
