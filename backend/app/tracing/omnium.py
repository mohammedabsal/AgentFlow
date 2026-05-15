from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import httpx

from app.core.config import settings


@dataclass(slots=True)
class TraceEvent:
    name: str
    payload: dict[str, Any]


class OmniumClient:
    def __init__(self) -> None:
        self.api_key = settings.omium_api_key
        # require explicit endpoint and api key
        self.endpoint = (settings.omium_endpoint or "").rstrip("/")
        self.enabled = bool(self.api_key and self.endpoint)
        if not self.enabled:
            logging.getLogger(__name__).debug(
                "Omnium disabled: set both OMIUM_API_KEY and OMIUM_ENDPOINT to enable telemetry"
            )
        self._client = httpx.Client(timeout=5.0)
        self._async_client = httpx.AsyncClient(timeout=5.0)

    def emit(self, event: TraceEvent) -> None:
        if not self.enabled:
            return
        try:
            url = f"{self.endpoint}/v1/events"
            body = {"name": event.name, "payload": event.payload}
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            resp = self._client.post(url, json=body, headers=headers)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - best-effort telemetry
            logging.getLogger(__name__).debug("Omnium emit failed: %s", exc)

    async def emit_async(self, event: TraceEvent) -> None:
        """Async version of emit for use in async contexts."""
        if not self.enabled:
            return
        try:
            url = f"{self.endpoint}/v1/events"
            body = {"name": event.name, "payload": event.payload}
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            resp = await self._async_client.post(url, json=body, headers=headers)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - best-effort telemetry
            logging.getLogger(__name__).debug("Omnium emit_async failed: %s", exc)


client = OmniumClient()


def trace_event(name: str, payload: dict[str, Any]) -> None:
    """Emit a trace event synchronously."""
    client.emit(TraceEvent(name=name, payload=payload))


async def emit_trace_event(
    event_type: str,
    properties: dict[str, Any],
    trace_id: str | None = None,
) -> None:
    """
    Emit a trace event asynchronously with standardized structure.
    
    Args:
        event_type: Type of event (e.g., 'run_started', 'step_completed')
        properties: Event-specific properties
        trace_id: Optional trace ID for correlation
    """
    payload = {
        "event_type": event_type,
        "properties": properties,
    }
    if trace_id:
        payload["trace_id"] = trace_id
    
    await client.emit_async(TraceEvent(name=event_type, payload=payload))
