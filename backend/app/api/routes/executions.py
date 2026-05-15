from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Execution
from app.database.session import get_db
from app.observability.event_store import execution_events
from app.queues.tasks import execute_workflow

router = APIRouter()


class ExecutionRequest(BaseModel):
    workflow_id: str
    input: dict[str, object] = {}


class ExecutionReadResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    input: dict[str, object]
    output: dict[str, object]
    state: dict[str, object]
    trace_id: str | None = None


def _serialize_execution(execution: Execution) -> ExecutionReadResponse:
    return ExecutionReadResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        input=dict(execution.input or {}),
        output=dict(execution.output or {}),
        state=dict(execution.state or {}),
        trace_id=execution.trace_id,
    )


@router.get("", response_model=list[ExecutionReadResponse])
def list_executions(db: Session = Depends(get_db)) -> list[ExecutionReadResponse]:
    executions = db.scalars(select(Execution).order_by(Execution.created_at.desc())).all()
    return [_serialize_execution(execution) for execution in executions]


@router.get("/{execution_id}", response_model=ExecutionReadResponse)
def get_execution(execution_id: str, db: Session = Depends(get_db)) -> ExecutionReadResponse:
    execution = db.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return _serialize_execution(execution)


@router.post("/run", response_model=ExecutionReadResponse, status_code=status.HTTP_201_CREATED)
def run_workflow(payload: ExecutionRequest, db: Session = Depends(get_db)) -> ExecutionReadResponse:
    execution = Execution(
        workflow_id=payload.workflow_id,
        status="queued",
        input=payload.input,
        state={"step": 0, "phase": "queued"},
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    execution_events.append(execution.id, "execution.queued", {"workflow_id": payload.workflow_id, "status": execution.status})
    if settings.execute_workflows_sync:
        execute_workflow.run(execution.id, payload.workflow_id, payload.input)
    else:
        execute_workflow.delay(execution.id, payload.workflow_id, payload.input)
    db.refresh(execution)
    return _serialize_execution(execution)
