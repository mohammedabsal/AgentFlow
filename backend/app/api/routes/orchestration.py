"""
API routes for orchestration and autonomous workflow execution.

Exposes:
- /api/orchestration/execute - Start autonomous workflow
- /api/orchestration/status - Get execution status
- /api/orchestration/ws - WebSocket streaming
- /api/orchestration/cancel - Cancel execution
- /api/orchestration/artifacts - Download artifacts
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from app.llm.client import Qwen3CoderClient
from app.orchestration.langgraph_engine import OrchestrationEngine
from app.streams.websocket_manager import connection_manager, handle_execution_websocket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestration", tags=["orchestration"])

# Global orchestration engine instance
_orchestration_engine: Optional[OrchestrationEngine] = None


def get_orchestration_engine() -> OrchestrationEngine:
    """Get or create orchestration engine."""
    global _orchestration_engine
    if _orchestration_engine is None:
        _orchestration_engine = OrchestrationEngine(llm_client=Qwen3CoderClient())
    return _orchestration_engine


# ============================================================================
# Request/Response Models
# ============================================================================


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute autonomous workflow."""

    project_name: str
    user_prompt: str
    model_preferences: Optional[dict[str, str]] = None
    enable_self_healing: bool = True
    max_iterations: int = 3
    webhook_url: Optional[str] = None


class ExecutionStatusResponse(BaseModel):
    """Current execution status."""

    execution_id: str
    status: str
    current_task: Optional[str]
    completed_tasks: list[str]
    progress: str
    logs: list[dict]


class ArtifactResponse(BaseModel):
    """Generated artifact."""

    artifact_id: str
    path: str
    content: str
    language: Optional[str]
    generated_by: Optional[str]


# ============================================================================
# Routes
# ============================================================================


@router.post("/execute")
async def execute_workflow(
    request: ExecuteWorkflowRequest,
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
) -> dict:
    """
    Start autonomous workflow execution.
    
    Returns execution_id for tracking and WebSocket connection.
    """
    try:
        # Define message callback for streaming
        async def stream_callback(message):
            await connection_manager.broadcast(execution_id, message)

        # Note: We'll use a task to run this in background
        # For now, return execution_id to client for WebSocket connection

        logger.info(f"Starting workflow: {request.project_name}")

        # Create plan first to validate input
        plan = await engine.create_execution_plan(
            project_id=f"project-{id(request)}",
            project_name=request.project_name,
            user_prompt=request.user_prompt,
        )

        # Return execution info for client to connect via WebSocket
        return {
            "execution_id": plan.plan_id,
            "project_name": request.project_name,
            "status": "initialized",
            "websocket_url": f"/api/orchestration/ws/{plan.plan_id}",
            "message": "Connect to WebSocket URL for real-time updates",
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status/{execution_id}")
async def get_execution_status(
    execution_id: str,
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
) -> ExecutionStatusResponse:
    """Get current status of an execution."""
    status_info = await engine.get_execution_status(execution_id)

    if not status_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    return ExecutionStatusResponse(**status_info)


@router.websocket("/ws/{execution_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    execution_id: str,
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
):
    """WebSocket endpoint for real-time execution streaming."""
    await handle_execution_websocket(websocket, execution_id)


@router.post("/cancel/{execution_id}")
async def cancel_execution(
    execution_id: str,
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
) -> dict:
    """Cancel an ongoing execution."""
    success = engine.stop_execution(execution_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    return {"execution_id": execution_id, "status": "cancelled"}


@router.get("/artifacts/{execution_id}")
async def list_artifacts(
    execution_id: str,
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
) -> list[ArtifactResponse]:
    """List all artifacts from an execution."""
    runtime = engine.active_executions.get(execution_id)

    if not runtime:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    artifacts = []
    for path, artifact in runtime.context.generated_artifacts.items():
        artifacts.append(
            ArtifactResponse(
                artifact_id=artifact.artifact_id,
                path=artifact.path,
                content=artifact.content[:500],  # Preview
                language=artifact.language,
                generated_by=artifact.generated_by.value if artifact.generated_by else None,
            )
        )

    return artifacts


@router.get("/artifacts/{execution_id}/{artifact_id}")
async def get_artifact(
    execution_id: str,
    artifact_id: str,
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
) -> ArtifactResponse:
    """Get specific artifact content."""
    runtime = engine.active_executions.get(execution_id)

    if not runtime:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    for path, artifact in runtime.context.generated_artifacts.items():
        if artifact.artifact_id == artifact_id:
            return ArtifactResponse(
                artifact_id=artifact.artifact_id,
                path=artifact.path,
                content=artifact.content,
                language=artifact.language,
                generated_by=artifact.generated_by.value if artifact.generated_by else None,
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
