from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    sender: str
    role: str
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)


class CollaborationPlan(BaseModel):
    goal: str
    tasks: list[str] = Field(default_factory=list)
    shared_state: dict[str, object] = Field(default_factory=dict)
