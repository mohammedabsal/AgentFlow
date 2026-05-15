from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class WorkspaceCreateRequest(BaseModel):
    name: str


@router.get("")
def list_workspaces() -> list[dict[str, object]]:
    return []


@router.post("")
def create_workspace(payload: WorkspaceCreateRequest) -> dict[str, object]:
    return {"id": "ws_demo", "name": payload.name}
