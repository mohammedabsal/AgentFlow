from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    workspace_id: str | None = None
    workspace_name: str = "Default Workspace"
    name: str
    prompt: str
    description: str | None = None
    project_metadata: dict[str, object] = Field(default_factory=dict)


class ProjectRead(BaseModel):
    id: str
    workspace_id: str
    name: str
    prompt: str
    description: str | None = None
    status: str
    project_metadata: dict[str, object] = Field(default_factory=dict)


class PlanStep(BaseModel):
    id: str
    title: str
    agent: str
    description: str
    dependencies: list[str] = Field(default_factory=list)


class PlanCreate(BaseModel):
    objective: str | None = None
    hints: dict[str, object] = Field(default_factory=dict)


class PlanRead(BaseModel):
    id: str
    project_id: str
    title: str
    objective: str
    roadmap: list[PlanStep] = Field(default_factory=list)
    stack: dict[str, list[str]] = Field(default_factory=dict)
    status: str


class RunCreate(BaseModel):
    prompt_override: str | None = None
    context: dict[str, object] = Field(default_factory=dict)


class RunRead(BaseModel):
    id: str
    project_id: str
    plan_id: str
    status: str
    prompt_input: dict[str, object] = Field(default_factory=dict)
    output: dict[str, object] = Field(default_factory=dict)
    state: dict[str, object] = Field(default_factory=dict)
    error: str | None = None
    trace_id: str | None = None


class ArtifactRead(BaseModel):
    id: str
    run_id: str
    kind: str
    path: str
    content: str
    artifact_metadata: dict[str, object] = Field(default_factory=dict)
