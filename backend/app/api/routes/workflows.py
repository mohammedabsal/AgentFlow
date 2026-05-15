from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Workflow
from app.database.session import get_db

router = APIRouter()


class WorkflowCreateRequest(BaseModel):
    workspace_id: str
    name: str
    description: str | None = None
    graph: dict[str, object] = Field(default_factory=dict)


class WorkflowReadResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str | None
    graph: dict[str, object]
    version: int


def _serialize_workflow(workflow: Workflow) -> WorkflowReadResponse:
    return WorkflowReadResponse(
        id=workflow.id,
        workspace_id=workflow.workspace_id,
        name=workflow.name,
        description=workflow.description,
        graph=dict(workflow.graph or {}),
        version=workflow.version,
    )


@router.get("", response_model=list[WorkflowReadResponse])
def list_workflows(db: Session = Depends(get_db)) -> list[WorkflowReadResponse]:
    workflows = db.scalars(select(Workflow).order_by(Workflow.created_at.desc())).all()
    return [_serialize_workflow(workflow) for workflow in workflows]


@router.post("", response_model=WorkflowReadResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreateRequest, db: Session = Depends(get_db)) -> WorkflowReadResponse:
    workflow = Workflow(
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        graph=payload.graph,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(workflow)


@router.get("/{workflow_id}", response_model=WorkflowReadResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)) -> WorkflowReadResponse:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return _serialize_workflow(workflow)
