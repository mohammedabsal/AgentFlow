from fastapi import APIRouter, Header, HTTPException

router = APIRouter()


@router.post("/{provider}")
def ingest_webhook(provider: str, x_signature: str | None = Header(default=None)) -> dict[str, str]:
    if provider not in {"github", "slack", "stripe", "crm"}:
        raise HTTPException(status_code=404, detail="Unsupported provider")
    return {"provider": provider, "signature": x_signature or "missing", "status": "accepted"}
