from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ApiKeyCreateRequest(BaseModel):
    workspace_id: str
    label: str


@router.get("")
def list_api_keys() -> list[dict[str, object]]:
    return []


@router.post("")
def create_api_key(payload: ApiKeyCreateRequest) -> dict[str, object]:
    return {"id": "key_demo", "workspace_id": payload.workspace_id, "label": payload.label}
