"""Prometheus metrics instrumentation for FastAPI application"""

import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.build_info import get_commit_sha

logger = logging.getLogger(__name__)

# =============================================================================
# HTTP LAYER METRICS
# =============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code", "commit_sha"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code", "commit_sha"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint", "commit_sha"],
)

# =============================================================================
# DATABASE OPERATIONS METRICS
# =============================================================================

database_errors_total = Counter(
    "database_errors_total",
    "Total number of database errors",
    ["error_code", "constraint", "constraint_type", "error_category", "commit_sha"],
)

database_connection_errors_total = Counter(
    "database_connection_errors_total",
    "Total number of database connection errors",
    ["commit_sha"],
)

# =============================================================================
# RETRY METRICS
# =============================================================================

retry_attempts_total = Counter(
    "retry_attempts_total",
    "Total number of retry attempts",
    ["operation", "commit_sha"],
)

retry_successes_total = Counter(
    "retry_successes_total",
    "Total number of successful retries",
    ["operation", "commit_sha"],
)

retry_failures_total = Counter(
    "retry_failures_total",
    "Total number of failed retries (max attempts exhausted)",
    ["operation", "commit_sha"],
)

# =============================================================================
# AUTHENTICATION METRICS
# =============================================================================

login_attempts_total = Counter(
    "login_attempts_total",
    "Total number of login attempts",
    ["success", "method", "commit_sha"],
)

authentication_errors_total = Counter(
    "authentication_errors_total",
    "Total number of authentication errors",
    ["error_message", "commit_sha"],
)


# =============================================================================
# PROMETHEUS MIDDLEWARE
# =============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics for Prometheus"""

    def __init__(self, app: ASGIApp, app_name: str = "codeleash") -> None:
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip metrics collection for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = self._get_endpoint(request)
        commit_sha = get_commit_sha()

        # Track requests in progress
        http_requests_in_progress.labels(
            method=method, endpoint=endpoint, commit_sha=commit_sha
        ).inc()

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            # Re-raise the exception
            raise e
        finally:
            # Always decrement in-progress counter
            http_requests_in_progress.labels(
                method=method, endpoint=endpoint, commit_sha=commit_sha
            ).dec()

            # Record request duration
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                commit_sha=commit_sha,
            ).observe(duration)

            # Increment request counter
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                commit_sha=commit_sha,
            ).inc()

        return response

    def _get_endpoint(self, request: Request) -> str:
        """Extract endpoint pattern from request path"""
        # Get the route pattern if available, otherwise use the path
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path_regex"):
                return route.path_regex.pattern
            elif hasattr(route, "path"):
                return route.path

        # Fallback to raw path with basic parameterization
        path = request.url.path

        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
        )

        # Replace numeric IDs with placeholder
        path = re.sub(r"/\d+", "/{id}", path)

        return path


# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================


def configure_metrics(app: FastAPI) -> None:
    """Configure Prometheus metrics for the FastAPI application"""

    # Add metrics middleware
    app.add_middleware(cast("type", PrometheusMiddleware), app_name="codeleash")


def start_metrics_server(
    port: int,
    environment: str,
    start_server_func: Callable[..., object] | None = None,
) -> None:
    """Start the Prometheus metrics HTTP server on the specified port"""
    if start_server_func is None:
        start_server_func = start_http_server

    try:
        start_server_func(port)
        logger.info(f"Metrics server started on port {port}")
    except OSError as e:
        if environment == "production":
            logger.error(f"Failed to start metrics server on port {port}: {e}")
            raise  # Crash in production
        else:
            logger.warning(
                f"Could not start metrics server on port {port}: {e}. "
                "Continuing without metrics server."
            )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


# Helper function to get commit SHA for metrics
def _get_commit_sha() -> str:
    """Get commit SHA for metric labels"""
    return get_commit_sha()


# Authentication Helpers
def record_login_attempt(success: bool, method: str = "password") -> None:
    """Record a login attempt"""
    login_attempts_total.labels(
        success=str(success).lower(), method=method, commit_sha=_get_commit_sha()
    ).inc()


def record_authentication_error(error_message: str) -> None:
    """Record an authentication error"""
    authentication_errors_total.labels(
        error_message=error_message, commit_sha=_get_commit_sha()
    ).inc()


def record_token_validation_failure(reason: str) -> None:
    """Record a token validation failure"""
    authentication_errors_total.labels(
        error_message=f"token_validation_{reason}", commit_sha=_get_commit_sha()
    ).inc()


# Database Operations Helpers
def record_database_error(
    error_code: str,
    constraint: str = "",
    constraint_type: str = "",
    error_category: str = "",
) -> None:
    """Record a database error"""
    database_errors_total.labels(
        error_code=error_code,
        constraint=constraint,
        constraint_type=constraint_type,
        error_category=error_category,
        commit_sha=_get_commit_sha(),
    ).inc()


def record_database_connection_error() -> None:
    """Record a database connection error"""
    database_connection_errors_total.labels(commit_sha=_get_commit_sha()).inc()


# Retry Helpers
def record_retry_attempt(operation: str) -> None:
    """Record a retry attempt"""
    retry_attempts_total.labels(operation=operation, commit_sha=_get_commit_sha()).inc()


def record_retry_success(operation: str) -> None:
    """Record a successful retry"""
    retry_successes_total.labels(
        operation=operation, commit_sha=_get_commit_sha()
    ).inc()


def record_retry_failed(operation: str) -> None:
    """Record a failed retry (max attempts exhausted)"""
    retry_failures_total.labels(operation=operation, commit_sha=_get_commit_sha()).inc()


# =============================================================================
# WORKER / QUEUE METRICS
# =============================================================================

worker_restarts_total = Counter(
    "worker_restarts_total",
    "Total number of worker restarts",
    ["reason", "commit_sha"],
)

queue_jobs_processed_total = Counter(
    "queue_jobs_processed_total",
    "Total number of queue jobs processed",
    ["queue", "status", "commit_sha"],
)

queue_job_duration_seconds = Histogram(
    "queue_job_duration_seconds",
    "Queue job processing duration in seconds",
    ["queue", "commit_sha"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
)

queue_depth = Gauge(
    "queue_depth",
    "Number of pending jobs in queue",
    ["queue"],
)


# Worker/Queue Helpers
def record_worker_restart(reason: str) -> None:
    """Record a worker restart event"""
    worker_restarts_total.labels(reason=reason, commit_sha=_get_commit_sha()).inc()


def record_queue_job_processed(queue: str, status: str) -> None:
    """Record a processed queue job"""
    queue_jobs_processed_total.labels(
        queue=queue, status=status, commit_sha=_get_commit_sha()
    ).inc()


def record_queue_job_duration(queue: str, duration: float) -> None:
    """Record queue job processing duration"""
    queue_job_duration_seconds.labels(
        queue=queue, commit_sha=_get_commit_sha()
    ).observe(duration)


def update_queue_depth_gauge(queue_name: str, depth: int) -> None:
    """Update the queue depth gauge for a specific queue"""
    queue_depth.labels(queue=queue_name).set(depth)
