from dataclasses import dataclass, field


@dataclass
class WebhookEvent:
    provider: str
    event_type: str
    payload: dict[str, object]


@dataclass
class WebhookInbox:
    events: list[WebhookEvent] = field(default_factory=list)

    def ingest(self, provider: str, event_type: str, payload: dict[str, object]) -> WebhookEvent:
        event = WebhookEvent(provider=provider, event_type=event_type, payload=payload)
        self.events.append(event)
        return event
