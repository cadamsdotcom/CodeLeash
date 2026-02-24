"""Centralized logging configuration."""

import logging

from opentelemetry import trace

from app.core.build_info import get_commit_sha


class TraceContextFilter(logging.Filter):
    """Add trace context and build info to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # check_unused_code: ignore
        """Add trace ID, span ID, and commit SHA to the log record."""
        # Add trace context
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            record.otelTraceID = format(span.get_span_context().trace_id, "032x")
            record.otelSpanID = format(span.get_span_context().span_id, "016x")
        else:
            record.otelTraceID = ""
            record.otelSpanID = ""

        # Add commit SHA
        record.commitSHA = get_commit_sha()
        return True


def configure_logging(level: int = logging.DEBUG) -> None:
    """
    Configure logging for the entire application.

    This function sets up the basic logging configuration and suppresses
    noisy HTTP client logs from httpx, httpcore, and related libraries.

    Args:
        level: The logging level to use (default: DEBUG)
    """
    # Configure basic logging with trace context
    handler = logging.StreamHandler()
    handler.addFilter(TraceContextFilter())

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - [commit=%(commitSHA)s trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s",
        handlers=[handler],
    )

    # Suppress noisy HTTP client logs - only show warnings and above
    logging.getLogger("fsevents").setLevel(logging.WARNING)
    logging.getLogger("h11").setLevel(logging.WARNING)
    logging.getLogger("h2").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("python_multipart").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
