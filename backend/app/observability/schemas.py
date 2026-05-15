from pydantic import BaseModel


class TraceNode(BaseModel):
    id: str
    parent_id: str | None = None
    name: str
    status: str


class TraceGraph(BaseModel):
    execution_id: str
    nodes: list[TraceNode] = []
    edges: list[dict[str, str]] = []
