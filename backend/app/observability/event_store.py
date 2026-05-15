from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class ExecutionEvent:
    execution_id: str
    type: str
    payload: dict[str, object]


@dataclass
class ExecutionEventStore:
    events: dict[str, list[ExecutionEvent]] = field(default_factory=lambda: defaultdict(list))
    lock: Lock = field(default_factory=Lock)

    def append(self, execution_id: str, event_type: str, payload: dict[str, object]) -> ExecutionEvent:
        event = ExecutionEvent(execution_id=execution_id, type=event_type, payload=payload)
        with self.lock:
            self.events[execution_id].append(event)
        return event

    def snapshot(self, execution_id: str) -> list[ExecutionEvent]:
        with self.lock:
            return list(self.events.get(execution_id, []))


execution_events = ExecutionEventStore()
