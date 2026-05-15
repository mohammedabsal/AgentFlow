from fastapi import APIRouter

router = APIRouter()


@router.get("/executions/{execution_id}/trace")
def execution_trace(execution_id: str) -> dict[str, object]:
    return {
        "execution_id": execution_id,
        "nodes": [],
        "edges": [],
        "logs": [],
        "tool_calls": [],
    }
