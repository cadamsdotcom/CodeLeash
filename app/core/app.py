"""FastAPI application factory and configuration."""

import logging
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.metrics import configure_metrics
from app.core.sentry import configure_sentry
from app.core.tracing import configure_tracing, instrument_fastapi
from app.routes import register_routes

# Configure logging for the entire application if not already configured
if not logging.getLogger().handlers:
    configure_logging()

# Configure tracing
configure_tracing()

# Configure Sentry for error tracking
configure_sentry()


# Custom StaticFiles class to disable caching for development
class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        self.cachecontrol = "max-age=0, no-cache, no-store, , must-revalidate"
        self.pragma = "no-cache"
        self.expires = "0"
        super().__init__(*args, **kwargs)

    def file_response(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        resp = super().file_response(*args, **kwargs)
        resp.headers.setdefault("Cache-Control", self.cachecontrol)
        resp.headers.setdefault("Pragma", self.pragma)
        resp.headers.setdefault("Expires", self.expires)
        return resp


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="CodeLeash",
        description="Development scaffold for CodeLeash",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        cast("type", CORSMiddleware),
        allow_origins=(
            settings.cors_origins if settings.environment == "production" else ["*"]
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    if settings.environment == "development":
        app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")
    else:
        app.mount("/static", StaticFiles(directory="static"), name="static")
        app.mount("/dist", StaticFiles(directory="dist"), name="dist")

    # Register custom exception handlers
    register_exception_handlers(app)

    # Register all routes
    register_routes(app)

    # Configure Prometheus metrics (includes /metrics endpoint)
    configure_metrics(app)

    # Instrument FastAPI with OpenTelemetry
    instrument_fastapi(app)

    return app


# Create the app instance
app = create_app()
