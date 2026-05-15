from dataclasses import dataclass, field


@dataclass(slots=True)
class ExecutionState:
    execution_id: str
    workflow_id: str
    current_node_id: str | None = None
    status: str = "queued"
    step_count: int = 0
    memory: dict[str, object] = field(default_factory=dict)
    outputs: dict[str, object] = field(default_factory=dict)
    history: list[dict[str, object]] = field(default_factory=list)
