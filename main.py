"""Main entry point for the CodeLeash application."""

import logging
import os
import threading

from dotenv import load_dotenv

from app.core.app import app  # noqa: F401
from app.core.config import settings
from app.core.metrics import start_metrics_server

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_metrics_in_thread() -> None:
    """Start metrics server in a separate thread to avoid blocking."""
    try:
        start_metrics_server(9091, settings.environment)
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        if settings.environment == "production":
            logger.error(
                "Metrics server failed in production, but continuing with main app"
            )


if __name__ == "__main__":
    import uvicorn

    # Start metrics server in background thread
    metrics_thread = threading.Thread(target=start_metrics_in_thread, daemon=True)
    metrics_thread.start()
    logger.info("Started metrics server thread")

    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting web server on 0.0.0.0:{port} in {settings.environment} mode")
    reload = settings.environment == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
