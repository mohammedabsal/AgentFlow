# AgentFlow Architecture

## System Overview

AgentFlow is a durable orchestration platform for autonomous AI software engineering. The core design principle is event-driven execution with full state persistence so prompts can become planned, generated, tested, repaired, and deployed applications.

## Backend Architecture

### Entry Layer

- FastAPI provides REST and WebSocket APIs.
- Authentication is JWT-based with workspace-scoped authorization.
- API keys support machine-to-machine integrations.
- The primary user entrypoint is a single prompt that creates or updates a project.

### Domain Modules

- `agents`: planner, prompt refinement, architect, frontend, backend, integration, debugging, testing, deployment, and monitoring roles.
- `workflows`: DAG definitions, branches, conditions, fallback paths, and workflow versioning.
- `runtime`: durable execution state machine and resume logic.
- `queues`: Celery workers and task dispatch.
- `tools`: sandboxed tool registry, code execution, Git operations, and schema validation.
- `memory`: workflow, shared, and vector memory interfaces.
- `webhooks`: external event ingestion and replay.
- `tracing`: Omnium and OpenTelemetry tracing bridge.
- `observability`: logs, traces, execution graphs, and runtime dashboards.
- `database`: SQLAlchemy models and session management.

### Execution Model

1. A user prompt creates a project and a run record.
2. The planner generates a roadmap and task graph.
3. Prompt refinement converts ambiguous instructions into structured specs.
4. Architecture generation defines folder structure, schemas, APIs, and UI surfaces.
5. Frontend and backend generation run in parallel.
6. Integration wires services, configuration, and environment variables.
7. Debugging loops repair build or runtime failures until the run is stable.
8. Testing validates unit, integration, and E2E behavior.
9. Deployment publishes the project to the target environment.
10. Monitoring watches for crashes and re-enters the repair loop when needed.

## Frontend Architecture

### App Shell

- Next.js App Router.
- TailwindCSS for design primitives.
- React Flow for visual DAG editing.
- Route-level views for chat, workspace, agents, executions, logs, integrations, and preview.
- Dark-mode-first, glassmorphism-inspired presentation.

### Client Data Flow

- REST endpoints load project, plan, and run state.
- WebSocket or SSE streams push live execution updates.
- UI state is kept minimal and derived from persisted run records.
- A timeline and execution graph visualize autonomous agent activity.

## Database Schema

Core tables:

- `projects`: tenant/project boundaries.
- `prompts`: raw user requests and refined specs.
- `plans`: generated task graphs and milestones.
- `agents`: agent configuration and role metadata.
- `runs`: runtime state, outputs, trace IDs, and status.
- `artifacts`: generated files, diffs, and build outputs.
- `events`: append-only event history for replay.
- `tool_calls`: inputs, outputs, status, latency, and trace linkage.
- `memory_records`: shared and project-scoped memory entries.
- `webhook_events`: ingested external events and replay state.
- `api_keys`: workspace-scoped machine credentials.
- `audit_logs`: security and administrative actions.

## Runtime and Queues

- Celery is used for long-running asynchronous execution.
- Redis acts as broker and transient coordination layer.
- PostgreSQL is the source of truth for durable state in production.
- SQLite supports local development without Docker.
- Dead-letter handling and retries are designed around idempotent task steps.

## Observability and Omnium

- Each run gets a unique execution ID and trace ID.
- Parent-child trace relationships preserve causal ordering.
- Tool calls, retries, webhook events, and agent hops emit trace events.
- Omnium is the workflow-level tracing backend; OpenTelemetry is the transport abstraction.
- The activity timeline feeds the UI console and progress tracker.

## Scalability Strategy

- Stateless API instances.
- Horizontally scaled worker pools.
- Queue-based backpressure.
- Durable checkpoints for resumption after failure.
- Rate limits and depth limits on execution chains.

## Security

- JWT and API key authentication.
- Secrets stored outside workflow payloads.
- Sandboxed tool execution.
- Timeout and depth limits.
- Schema validation for all structured agent communication.
- Multi-tenant isolation for projects and runtime artifacts.
