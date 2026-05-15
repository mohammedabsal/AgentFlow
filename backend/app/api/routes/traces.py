from fastapi import APIRouter

router = APIRouter()


@router.get("/{execution_id}")
def get_trace(execution_id: str) -> dict[str, object]:
    return {
        "execution_id": execution_id,
        "nodes": [],
        "edges": [],
        "status": "empty",
    }
