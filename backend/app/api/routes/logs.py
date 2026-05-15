from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_logs(execution_id: str | None = None) -> list[dict[str, object]]:
    return [{"execution_id": execution_id, "level": "info", "message": "Execution log stream placeholder"}]
