from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Artifact, Plan, Project, Run, Workspace
from app.llm.qwen_client import Qwen3CoderClient
from app.database.session import get_db
from app.orchestration.service import AutonomousProjectService
from app.schemas.platform import ArtifactRead, PlanCreate, PlanRead, ProjectCreate, ProjectRead, RunCreate, RunRead
from app.streams import stream_manager
from app.tracing.omnium import emit_trace_event
from app.product_builder import PackagingService

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize_project(project: Project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        prompt=project.prompt,
        description=project.description,
        status=project.status,
        project_metadata=dict(project.project_metadata or {}),
    )


def _serialize_plan(plan: Plan) -> PlanRead:
    from app.schemas.platform import PlanStep

    return PlanRead(
        id=plan.id,
        project_id=plan.project_id,
        title=plan.title,
        objective=plan.objective,
        roadmap=[PlanStep(**step) for step in (plan.roadmap or [])],
        stack={key: list(value) for key, value in (plan.stack or {}).items()},
        status=plan.status,
    )


def _serialize_run(run: Run) -> RunRead:
    return RunRead(
        id=run.id,
        project_id=run.project_id,
        plan_id=run.plan_id,
        status=run.status,
        prompt_input=dict(run.prompt_input or {}),
        output=dict(run.output or {}),
        state=dict(run.state or {}),
        error=run.error,
        trace_id=run.trace_id,
    )


def _serialize_artifact(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead(
        id=artifact.id,
        run_id=artifact.run_id,
        kind=artifact.kind,
        path=artifact.path,
        content=artifact.content,
        artifact_metadata=dict(artifact.artifact_metadata or {}),
    )


def _service(db: Session) -> AutonomousProjectService:
    return AutonomousProjectService(db)


def _llm_client() -> Qwen3CoderClient:
    return Qwen3CoderClient()


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    projects = db.scalars(select(Project).order_by(Project.created_at.desc())).all()
    return [_serialize_project(project) for project in projects]


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    service = _service(db)
    project = service.create_project(
        workspace_id=payload.workspace_id,
        workspace_name=payload.workspace_name,
        name=payload.name,
        prompt=payload.prompt,
        description=payload.description,
        project_metadata=payload.project_metadata,
    )
    return _serialize_project(project)


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return _serialize_project(project)


@router.post("/projects/{project_id}/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(project_id: str, payload: PlanCreate | None = None, db: Session = Depends(get_db)) -> PlanRead:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    service = _service(db)
    plan, _ = service.build_plan(project, objective=(payload.objective if payload else None))
    return _serialize_plan(plan)


@router.get("/projects/{project_id}/plans", response_model=list[PlanRead])
def list_project_plans(project_id: str, db: Session = Depends(get_db)) -> list[PlanRead]:
    plans = db.scalars(select(Plan).where(Plan.project_id == project_id).order_by(Plan.created_at.desc())).all()
    return [_serialize_plan(plan) for plan in plans]


@router.post("/projects/{project_id}/runs", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(project_id: str, payload: RunCreate | None = None, db: Session = Depends(get_db)) -> RunRead:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    service = _service(db)
    plans = db.scalars(select(Plan).where(Plan.project_id == project_id).order_by(Plan.created_at.desc())).all()
    objective = payload.prompt_override if payload and payload.prompt_override else None
    plan, plan_snapshot = service.build_plan(project, objective=objective) if not plans or objective else (plans[0], service.engine.build_plan(project.id, project.name, plans[0].objective))
    run = service.execute_project(project, plan, plan_snapshot)
    return _serialize_run(run)


@router.get("/runs", response_model=list[RunRead])
def list_runs(db: Session = Depends(get_db)) -> list[RunRead]:
    runs = db.scalars(select(Run).order_by(Run.created_at.desc())).all()
    return [_serialize_run(run) for run in runs]


@router.get("/runs/{run_id}", response_model=RunRead)
def get_run(run_id: str, db: Session = Depends(get_db)) -> RunRead:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return _serialize_run(run)


@router.post("/runs/{run_id}/retry", response_model=RunRead)
def retry_run(run_id: str, db: Session = Depends(get_db)) -> RunRead:
    result = _service(db).retry_run(run_id)
    return _serialize_run(result.run)


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactRead])
def list_run_artifacts(run_id: str, db: Session = Depends(get_db)) -> list[ArtifactRead]:
    artifacts = db.scalars(select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at.asc())).all()
    return [_serialize_artifact(artifact) for artifact in artifacts]


@router.get("/runs/{run_id}/download")
def download_run_project(run_id: str, db: Session = Depends(get_db)) -> FileResponse:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    packager = PackagingService()
    archive = packager.archive_path(run_id)
    if not archive.exists():
        try:
            archive = packager.create_zip(run_id=run_id, project_id=run.project_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return FileResponse(
        path=str(archive),
        media_type="application/zip",
        filename=f"agentflow-run-{run_id}.zip",
    )


@router.get("/runs/{run_id}/stream")
async def stream_run_progress(run_id: str, db: Session = Depends(get_db)):
    """
    Stream real-time progress updates for a run via Server-Sent Events (SSE).
    
    Events emitted:
    - run_started: Run execution started
    - step_started: Agent task started
    - step_completed: Agent task completed
    - run_completed: Run execution completed
    """
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    # Emit trace event to Omium
    try:
        await emit_trace_event(
            event_type="run_stream_started",
            properties={
                "run_id": run_id,
                "project_id": run.project_id,
                "plan_id": run.plan_id,
            },
            trace_id=run.trace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to emit trace event: {e}")

    async def event_generator():
        async for event in stream_manager.stream_run_progress(run_id, run):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/{run_id}/logs/stream")
async def stream_run_logs(run_id: str, db: Session = Depends(get_db)):
    """
    Stream live logs for a run via Server-Sent Events (SSE).
    
    Events emitted:
    - log_entry: Individual log message with level and timestamp
    """
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    # Emit trace event to Omium
    try:
        await emit_trace_event(
            event_type="run_logs_stream_started",
            properties={
                "run_id": run_id,
                "project_id": run.project_id,
            },
            trace_id=run.trace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to emit trace event: {e}")

    async def event_generator():
        async for event in stream_manager.stream_run_logs(run_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/{run_id}/artifacts/stream")
async def stream_run_artifacts(run_id: str, db: Session = Depends(get_db)):
    """
    Stream artifacts as they are generated via Server-Sent Events (SSE).
    
    Events emitted:
    - artifacts_start: Streaming started
    - artifact_generated: Individual artifact generated
    - artifacts_complete: Streaming complete
    """
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    # Get artifacts for this run
    artifacts = db.scalars(select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at.asc())).all()

    # Emit trace event to Omium
    try:
        await emit_trace_event(
            event_type="run_artifacts_stream_started",
            properties={
                "run_id": run_id,
                "artifact_count": len(artifacts),
            },
            trace_id=run.trace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to emit trace event: {e}")

    async def event_generator():
        async for event in stream_manager.stream_artifacts(run_id, artifacts):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models/installed")
def list_installed_models() -> dict[str, object]:
    client = _llm_client()
    return client.list_installed_models()


@router.websocket("/runs/ws/{run_id}")
async def stream_run_websocket(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "run_id": run_id})

    async def forward(event: dict[str, object]) -> None:
        await websocket.send_json(event)

    stream_manager.subscribe(run_id, forward)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
    finally:
        stream_manager.unsubscribe(run_id, forward)
