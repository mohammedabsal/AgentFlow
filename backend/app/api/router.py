from fastapi import APIRouter

from app.api.routes import auth, executions, health, workflows, webhooks, observability, agents, workspaces, api_keys, logs, traces, streams, platform, orchestration

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(platform.router, tags=["platform"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(streams.router, tags=["streams"])
api_router.include_router(orchestration.router, tags=["orchestration"])
