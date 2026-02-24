"""OpenTelemetry tracing configuration."""

import logging
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.build_info import get_commit_sha
from app.core.config import settings

logger = logging.getLogger(__name__)


def configure_tracing() -> None:
    """Configure OpenTelemetry tracing for the application."""
    service_name = os.getenv("OTEL_SERVICE_NAME", "codeleash")

    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: "0.1.0",
            "service.environment": settings.environment,
            "service.commit": get_commit_sha(),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    otlp_configured = otlp_endpoint is not None and otlp_endpoint != ""

    if otlp_configured:
        headers = {}
        otlp_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        if otlp_headers:
            for header in otlp_headers.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    headers[key.strip()] = value.strip()

        timeout = int(os.getenv("OTEL_EXPORTER_TIMEOUT", "10"))

        otlp_exporter = OTLPSpanExporter(
            headers=headers,
            timeout=timeout,
        )

        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        logger.info(
            f"OpenTelemetry tracing export enabled for {settings.environment} "
            f"with endpoint: {otlp_endpoint} and service name: {service_name}"
        )
    else:
        logger.info(
            f"OpenTelemetry tracing configured without export for {settings.environment} environment. "
            f"Set OTEL_EXPORTER_OTLP_ENDPOINT to enable tracing export."
        )

    logging_instrumentor = LoggingInstrumentor()
    if logging_instrumentor:
        logging_instrumentor.instrument(set_logging_format=True)

    httpx_instrumentor = HTTPXClientInstrumentor()
    if httpx_instrumentor:
        httpx_instrumentor.instrument()


def instrument_fastapi(app: FastAPI) -> None:
    """Instrument FastAPI application with OpenTelemetry."""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumented with OpenTelemetry")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_current_trace_id() -> str:
    """Get the current trace ID as a string."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return ""


def get_current_span_id() -> str:
    """Get the current span ID as a string."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return ""
