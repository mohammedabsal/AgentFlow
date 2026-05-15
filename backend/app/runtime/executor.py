from __future__ import annotations

from dataclasses import asdict

from app.runtime.state import ExecutionState
from app.tracing.omnium import trace_event


class WorkflowExecutor:
    def __init__(self, queue_client: object | None = None) -> None:
        self.queue_client = queue_client

    def start(self, execution_state: ExecutionState) -> dict[str, object]:
        execution_state.status = "running"
        execution_state.step_count += 1
        execution_state.current_node_id = execution_state.current_node_id or "start"
        execution_state.history.append({"event": "execution_started", "execution_id": execution_state.execution_id})
        trace_event("execution.started", asdict(execution_state))
        return {"execution_id": execution_state.execution_id, "status": execution_state.status}

    def resume(self, execution_state: ExecutionState) -> dict[str, object]:
        execution_state.history.append({"event": "execution_resumed", "execution_id": execution_state.execution_id})
        trace_event("execution.resumed", asdict(execution_state))
        return {"execution_id": execution_state.execution_id, "status": execution_state.status}
