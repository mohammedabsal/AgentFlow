from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    id: str
    type: str
    config: dict[str, object] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: str | None = None


class WorkflowGraph(BaseModel):
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowCreate(BaseModel):
    workspace_id: str
    name: str
    description: str | None = None
    graph: WorkflowGraph
