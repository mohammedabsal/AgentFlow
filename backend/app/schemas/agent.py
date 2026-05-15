from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str
    role: str
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    model_provider: str = "openai"
    memory_config: dict[str, object] = Field(default_factory=dict)
    retry_policy: dict[str, object] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    workspace_id: str


class AgentRead(AgentBase):
    id: str
    workspace_id: str
