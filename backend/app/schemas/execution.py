from pydantic import BaseModel, Field


class ExecutionStart(BaseModel):
    workflow_id: str
    input: dict[str, object] = Field(default_factory=dict)


class ExecutionRead(BaseModel):
    id: str
    workflow_id: str
    status: str
    input: dict[str, object]
    output: dict[str, object]
    state: dict[str, object]
    trace_id: str | None = None
