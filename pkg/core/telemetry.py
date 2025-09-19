from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry(app, service_name: str = "recipes-api", endpoint: str = None):
    """Setup OpenTelemetry with OTLP exporter for Grafana."""

    # Create resource with service info
    resource = Resource.create({"service.name": service_name})

    # Setup tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Add OTLP exporter if endpoint is provided
    if endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    return provider