"""Streaming and real-time updates for runs and logs."""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Callable

from app.database.models import Run
from app.orchestration.contracts import RunOutcomeContract

logger = logging.getLogger(__name__)


class RunEventStreamManager:
    """Manages real-time event streaming for run execution."""

    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, run_id: str, callback: Callable) -> None:
        """Subscribe to events for a specific run."""
        if run_id not in self.subscribers:
            self.subscribers[run_id] = []
        self.subscribers[run_id].append(callback)

    def unsubscribe(self, run_id: str, callback: Callable) -> None:
        """Unsubscribe from events for a specific run."""
        if run_id in self.subscribers and callback in self.subscribers[run_id]:
            self.subscribers[run_id].remove(callback)

    async def emit_event(
        self,
        run_id: str,
        event_type: str,
        data: dict,
        trace_id: str | None = None,
    ) -> None:
        """Emit an event to all subscribers of a run."""
        event = {
            "type": event_type,
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "trace_id": trace_id,
        }

        if run_id in self.subscribers:
            for callback in self.subscribers[run_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error calling subscriber callback: {e}")

    async def stream_run_progress(
        self, run_id: str, run: Run
    ) -> AsyncGenerator[str, None]:
        """
        Stream SSE events for a run's execution progress.
        Yields SSE-formatted strings.
        """
        # Emit run started event
        yield self._format_sse(
            "run_started",
            {
                "run_id": run_id,
                "status": run.status,
                "created_at": run.created_at.isoformat(),
            },
        )

        # Simulate streaming steps (in real implementation, these come from task queue)
        steps = run.state.get("steps", []) if run.state else []
        for i, step in enumerate(steps):
            await asyncio.sleep(0.5)  # Small delay to simulate work

            yield self._format_sse(
                "step_started",
                {
                    "step_index": i,
                    "step": step.get("title", ""),
                    "agent": step.get("agent", ""),
                },
            )

            await asyncio.sleep(1.0)

            yield self._format_sse(
                "step_completed",
                {
                    "step_index": i,
                    "step": step.get("title", ""),
                    "output": f"Completed: {step.get('description', '')}",
                },
            )

        # Emit run completed event
        yield self._format_sse(
            "run_completed",
            {
                "run_id": run_id,
                "status": run.status,
                "updated_at": run.updated_at.isoformat(),
                "artifacts": run.output.get("summary", ""),
            },
        )

    def _format_sse(self, event_type: str, data: dict) -> str:
        """Format event as Server-Sent Event."""
        lines = [
            f"event: {event_type}",
            f"data: {json.dumps(data)}",
            "",
        ]
        return "\n".join(lines) + "\n"

    async def stream_run_logs(self, run_id: str) -> AsyncGenerator[str, None]:
        """
        Stream SSE events for run logs.
        Yields SSE-formatted log entries.
        """
        # Emit initial log message
        yield self._format_sse(
            "log_entry",
            {
                "level": "info",
                "message": f"Started streaming logs for run {run_id}",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Simulate log streaming (in real implementation, comes from task queue)
        log_messages = [
            ("info", "Initializing project..."),
            ("info", "Generating plan..."),
            ("info", "Starting agent tasks..."),
            ("debug", "Agent: Prompt Refinement Agent"),
            ("debug", "Processing requirements..."),
            ("info", "Plan generated successfully"),
            ("info", "Starting execution..."),
            ("debug", "Agent: Architect Agent"),
            ("info", "Architecture designed"),
            ("info", "Execution completed"),
        ]

        for level, message in log_messages:
            await asyncio.sleep(0.3)
            yield self._format_sse(
                "log_entry",
                {
                    "level": level,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def stream_artifacts(self, run_id: str, artifacts) -> AsyncGenerator[str, None]:
        """
        Stream SSE events for generated artifacts.
        Yields SSE-formatted artifact updates.
        """
        yield self._format_sse(
            "artifacts_start",
            {
                "run_id": run_id,
                "total_artifacts": len(artifacts),
            },
        )

        for i, artifact in enumerate(artifacts):
            await asyncio.sleep(0.2)

            yield self._format_sse(
                "artifact_generated",
                {
                    "index": i,
                    "kind": artifact.kind if hasattr(artifact, "kind") else artifact.get("kind"),
                    "path": artifact.path if hasattr(artifact, "path") else artifact.get("path"),
                    "size_bytes": len(
                        artifact.content if hasattr(artifact, "content") else artifact.get("content", "")
                    ),
                },
            )

        yield self._format_sse(
            "artifacts_complete",
            {
                "run_id": run_id,
                "total_artifacts": len(artifacts),
            },
        )


# Global instance
stream_manager = RunEventStreamManager()
