"""Sentry configuration and initialization for error tracking."""

import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def configure_sentry() -> None:
    """Configure Sentry for error tracking."""

    if not settings.sentry_dsn or settings.environment != "production":
        return

    logger.info(f"Initializing Sentry for environment: {settings.environment}")

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        send_default_pii=False,
    )

    logger.info("Sentry initialized successfully")
