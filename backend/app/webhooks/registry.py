from dataclasses import dataclass, field


@dataclass
class WebhookSubscription:
    provider: str
    event_type: str
    workspace_id: str
    secret_ref: str | None = None


@dataclass
class WebhookRegistry:
    subscriptions: list[WebhookSubscription] = field(default_factory=list)

    def register(self, subscription: WebhookSubscription) -> None:
        self.subscriptions.append(subscription)
