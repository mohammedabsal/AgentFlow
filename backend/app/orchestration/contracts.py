from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Agent & Execution State
# ============================================================================


class AgentRole(str, Enum):
    """Available agent roles in the multi-agent system."""

    PROMPT_REFINER = "prompt_refiner"
    RESEARCH = "research"
    PLANNER = "planner"
    ARCHITECT = "architect"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    API = "api"
    DEVOPS = "devops"
    TESTING = "testing"
    SELF_HEALING = "self_healing"


class ExecutionStatus(str, Enum):
    """Execution status lifecycle."""

    PENDING = "pending"
    RUNNING = "running"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class WorkflowNodeType(str, Enum):
    """LangGraph workflow node types."""

    AGENT = "agent"
    TOOL = "tool"
    DECISION = "decision"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


# ============================================================================
# Task & Execution Planning
# ============================================================================


class TaskContract(BaseModel):
    """Single executable task in a workflow."""

    id: str
    title: str
    description: str
    agent: AgentRole
    dependencies: list[str] = Field(default_factory=list)
    parallel_with: list[str] = Field(default_factory=list)
    estimated_tokens: int = 0
    retry_count: int = 3
    timeout_seconds: int = 3600
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlanContract(BaseModel):
    """Complete execution plan with dependencies and parallelization."""

    plan_id: str
    project_id: str
    project_name: str
    user_prompt: str
    refined_prompt: str
    objective: str
    tech_stack: dict[str, list[str]] = Field(default_factory=dict)
    tasks: list[TaskContract] = Field(default_factory=list)
    execution_graph: dict[str, Any] = Field(default_factory=dict)
    estimated_total_tokens: int = 0
    risks: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlanStepContract(BaseModel):
    """Backward compatible plan step."""

    id: str
    title: str
    agent: str
    description: str
    dependencies: list[str] = Field(default_factory=list)


class GeneratedPlanContract(BaseModel):
    """Backward compatible generated plan."""

    project_id: str
    project_name: str
    objective: str
    stack: dict[str, list[str]] = Field(default_factory=dict)
    steps: list[PlanStepContract] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ============================================================================
# Code Generation & Artifacts
# ============================================================================


class ArtifactType(str, Enum):
    """Type of artifact generated."""

    FILE = "file"
    DIRECTORY = "directory"
    SCHEMA = "schema"
    COMPONENT = "component"
    TEST = "test"
    CONFIG = "config"


class GeneratedArtifactContract(BaseModel):
    """Generated code/config artifact."""

    artifact_id: str
    kind: ArtifactType
    path: str
    content: str
    language: Optional[str] = None
    generated_by: Optional[AgentRole] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    artifact_metadata: dict[str, Any] = Field(default_factory=dict)
    is_executable: bool = False


class CodeGenerationRequest(BaseModel):
    """Request to generate code."""

    task_id: str
    agent: AgentRole
    context: str
    requirements: str
    existing_files: list[str] = Field(default_factory=list)
    target_language: str = "python"


class CodeGenerationResponse(BaseModel):
    """Response from code generation."""

    request_id: str
    artifacts: list[GeneratedArtifactContract] = Field(default_factory=list)
    tokens_used: int = 0
    generation_time_ms: int = 0
    quality_score: float = 0.0


# ============================================================================
# Execution & Streaming
# ============================================================================


class ExecutionLogEntry(BaseModel):
    """Log entry from execution."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str  # "debug", "info", "warning", "error"
    source: str  # agent, task, system, tool
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionStreamMessage(BaseModel):
    """WebSocket message for streaming execution."""

    type: str  # "status", "log", "artifact", "progress", "error", "complete"
    execution_id: str
    agent: Optional[AgentRole] = None
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskExecutionState(BaseModel):
    """State during task execution."""

    task_id: str
    execution_id: str
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent: AgentRole
    input_context: dict[str, Any] = Field(default_factory=dict)
    output_artifacts: list[GeneratedArtifactContract] = Field(default_factory=list)
    logs: list[ExecutionLogEntry] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    retry_count: int = 0


class WorkspaceExecutionResult(BaseModel):
    """Result from executing code in Docker workspace."""

    execution_id: str
    workspace_id: str
    command: str
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    duration_ms: int = 0
    artifacts_created: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ============================================================================
# Self-Healing Loop
# ============================================================================


class ErrorAnalysisContract(BaseModel):
    """Analysis of an error for fixing."""

    error_id: str
    error_message: str
    error_type: str
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    context: str
    severity: str  # "critical", "warning", "info"
    suggested_fix: str


class AutoFix(BaseModel):
    """Automatic fix to apply."""

    fix_id: str
    error_id: str
    file_path: str
    original_content: str
    fixed_content: str
    explanation: str
    confidence: float  # 0.0 to 1.0


class SelfHealingLoopContract(BaseModel):
    """Self-healing execution loop."""

    loop_id: str
    execution_id: str
    iteration: int
    error_analysis: ErrorAnalysisContract
    applied_fixes: list[AutoFix] = Field(default_factory=list)
    rerun_result: Optional[WorkspaceExecutionResult] = None
    resolved: bool = False


# ============================================================================
# Run Execution
# ============================================================================


class RunOutcomeContract(BaseModel):
    """Complete run outcome."""

    run_id: str
    execution_id: str
    project_id: str
    status: ExecutionStatus
    summary: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    artifacts: list[GeneratedArtifactContract] = Field(default_factory=list)
    logs: list[ExecutionLogEntry] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_tokens_used: int = 0
    cost_estimate: float = 0.0
    self_healing_loops: list[SelfHealingLoopContract] = Field(default_factory=list)
    task_results: dict[str, TaskExecutionState] = Field(default_factory=dict)


class ProjectRunRequest(BaseModel):
    """Request to start a new project run."""

    project_name: str
    user_prompt: str
    model_preferences: dict[str, str] = Field(
        default_factory=lambda: {
            "planning": "gemini-2.5-pro",
            "coding": "qwen2.5-coder",
            "fast": "groq-llama3.1-8b",
        }
    )
    enable_self_healing: bool = True
    max_iterations: int = 3
    webhook_url: Optional[str] = None


class WorkspaceMetadata(BaseModel):
    """Metadata about a generated workspace."""

    workspace_id: str
    project_id: str
    run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)
    mount_path: str
    docker_image: str = "ubuntu:22.04"
    exposed_ports: list[int] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    status: str = "created"  # created, running, stopped, deleted
