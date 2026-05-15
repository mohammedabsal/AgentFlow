from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Agent
from app.database.session import get_db

router = APIRouter()


class AgentCreateRequest(BaseModel):
    workspace_id: str
    name: str
    role: str
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    model_provider: str = "openai"
    memory_config: dict[str, object] = Field(default_factory=dict)
    retry_policy: dict[str, object] = Field(default_factory=dict)


class AgentReadResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    role: str
    system_prompt: str
    tools: list[str]
    model_provider: str
    memory_config: dict[str, object]
    retry_policy: dict[str, object]


def _serialize_agent(agent: Agent) -> AgentReadResponse:
    return AgentReadResponse(
        id=agent.id,
        workspace_id=agent.workspace_id,
        name=agent.name,
        role=agent.role,
        system_prompt=agent.system_prompt,
        tools=list(agent.tools or []),
        model_provider=agent.model_provider,
        memory_config=dict(agent.memory_config or {}),
        retry_policy=dict(agent.retry_policy or {}),
    )


@router.get("", response_model=list[AgentReadResponse])
def list_agents(db: Session = Depends(get_db)) -> list[AgentReadResponse]:
    agents = db.scalars(select(Agent).order_by(Agent.created_at.desc())).all()
    return [_serialize_agent(agent) for agent in agents]


@router.post("", response_model=AgentReadResponse, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreateRequest, db: Session = Depends(get_db)) -> AgentReadResponse:
    agent = Agent(
        workspace_id=payload.workspace_id,
        name=payload.name,
        role=payload.role,
        system_prompt=payload.system_prompt,
        tools=payload.tools,
        model_provider=payload.model_provider,
        memory_config=payload.memory_config,
        retry_policy=payload.retry_policy,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _serialize_agent(agent)


@router.get("/{agent_id}", response_model=AgentReadResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)) -> AgentReadResponse:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return _serialize_agent(agent)
