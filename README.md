# AgentFlow

AgentFlow is an autonomous AI software engineering platform inspired by Lovable. It turns a single user prompt into a planned, built, tested, fixed, and deployable full-stack application with minimal user interaction, using a locally downloaded Qwen3-Coder model for orchestration.

## What this scaffold includes

- FastAPI backend with modular routing, auth, workflow, execution, webhook, tool, tracing, and memory layers.
- Celery + Redis execution queue skeleton.
- SQLite-first local development defaults, with PostgreSQL-compatible persistence for production.
- Next.js + TypeScript + Tailwind frontend shell with dashboard, builder, agent, execution, logs, and integrations routes.
- Omnium/OpenTelemetry tracing integration points.
- Local Qwen3-Coder model orchestration and artifact generation.
- A documented product vision for the autonomous app-generation workflow.

## Architecture

### Backend

- `backend/app/api`: REST and WebSocket entrypoints.
- `backend/app/agents`: agent definitions, planner-worker orchestration, and collaboration primitives.
- `backend/app/workflows`: DAG definitions, persistence, and workflow CRUD.
- `backend/app/runtime`: resumable workflow execution engine.
- `backend/app/queues`: Celery app, task submission, and worker lifecycle.
- `backend/app/tools`: tool registry, schema validation, and sandbox hooks.
- `backend/app/tracing`: Omnium and OpenTelemetry bridge.
- `backend/app/memory`: workflow, agent, and execution memory services.
- `backend/app/webhooks`: inbound webhook ingestion and replay.
- `backend/app/observability`: logs, traces, metrics, and execution views.
- `backend/app/database`: SQLAlchemy models, session management, and migrations entrypoints.

### Frontend

- `frontend/src/app`: dashboard, builder, agent, execution, and integration pages.
- `frontend/src/components`: shared UI primitives and graph components.
- `frontend/src/graph`: React Flow workflow editor surface.
- `frontend/src/services`: API client and realtime subscriptions.
- `frontend/src/hooks`: data-fetching and realtime hooks.
- `frontend/src/store`: client state for execution and graph editing.

## Local development

1. Start the backend:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

3. Optional: run the queue worker if you need async execution.

```bash
cd backend
celery -A app.queues.celery_app worker --loglevel=info
```

## Product vision

See [docs/platform-vision.md](docs/platform-vision.md) for the full Lovable-style autonomous app platform spec, including:

- The agent graph and execution loop.
- Frontend and backend stack choices.
- Data model and API contracts.
- Deployment and testing strategy.
- Self-healing and monitoring behavior.

## Production notes

- Use stateless API pods and horizontally scaled Celery workers.
- Persist every state transition in PostgreSQL for production.
- Keep execution steps idempotent and replayable.
- Enforce timeouts, depth limits, and sandboxed tool execution.
- Export traces to Omnium and OpenTelemetry-compatible backends.
