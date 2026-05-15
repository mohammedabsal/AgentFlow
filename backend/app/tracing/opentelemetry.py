from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class InMemorySpanExporter:
    def export(self, spans):
        return spans

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis: int = 30000):
        return True


def configure_tracing(service_name: str = "agentflow") -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    provider.add_span_processor(SimpleSpanProcessor(InMemorySpanExporter()))
