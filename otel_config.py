"""
OpenTelemetry configuration and initialization module.

This module handles all OpenTelemetry setup including:
- Tracer provider initialization
- OTLP exporter configuration
- Auto-instrumentation setup
- Environment-based configuration
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPExporter


def init_telemetry(service_name: str, service_version: str = "1.0.0") -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing for the application.

    Configuration via environment variables:
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (default: http://localhost:4318)
    - OTEL_EXPORTER_OTLP_PROTOCOL: Protocol to use - 'grpc' or 'http' (default: http)
    - OTEL_TRACES_ENABLED: Enable/disable tracing (default: true)
    - OTEL_CONSOLE_EXPORTER: Also export to console for debugging (default: false)

    Args:
        service_name: Name of the service being instrumented
        service_version: Version of the service

    Returns:
        Configured tracer instance
    """
    traces_enabled = os.getenv("OTEL_TRACES_ENABLED", "true").lower() == "true"

    if not traces_enabled:
        print(f"[OTEL] Tracing disabled for {service_name}")
        trace.set_tracer_provider(TracerProvider(resource=Resource.create({SERVICE_NAME: service_name})))
        return trace.get_tracer(__name__)

    # Configure resource attributes
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    otlp_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http").lower()

    try:
        if otlp_protocol == "http":
            # HTTP exporter expects endpoints with /v1/traces path
            if not otlp_endpoint.endswith("/v1/traces"):
                otlp_endpoint = f"{otlp_endpoint.rstrip('/')}/v1/traces"
            exporter = HTTPExporter(endpoint=otlp_endpoint)
            print(f"[OTEL] Using HTTP OTLP exporter: {otlp_endpoint}")
        else:
            exporter = GRPCExporter(endpoint=otlp_endpoint)
            print(f"[OTEL] Using gRPC OTLP exporter: {otlp_endpoint}")

        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception as e:
        print(f"[OTEL] Warning: Failed to configure OTLP exporter: {e}")
        print(f"[OTEL] Traces will not be exported. Check OTEL_EXPORTER_OTLP_ENDPOINT configuration.")

    # Optionally add console exporter for debugging
    if os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower() == "true":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        print(f"[OTEL] Console exporter enabled")

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    print(f"[OTEL] Tracing initialized for {service_name} v{service_version}")

    return trace.get_tracer(__name__)


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance for creating manual spans.

    Args:
        name: Name for the tracer (typically __name__ of the calling module)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
