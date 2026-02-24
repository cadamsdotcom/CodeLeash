#!/usr/bin/env python3
"""
Queue worker entry point for processing background jobs.
"""

import asyncio
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import record_worker_restart, start_metrics_server
from app.core.sentry import configure_sentry
from app.core.tracing import configure_tracing
from app.core.worker_dependencies import create_queue_worker

# Load environment variables from .env file
load_dotenv()


def _should_enable_hot_reload() -> bool:
    """Determine if hot reload should be enabled"""
    environment = os.getenv("ENVIRONMENT", "development")

    # Only enable hot reload in development mode
    return environment == "development"


class WorkerReloadHandler(FileSystemEventHandler):
    """File system event handler for hot reloading the worker"""

    def __init__(self, restart_event: asyncio.Event) -> None:
        self.restart_event = restart_event
        self.last_reload_time = 0.0
        self.reload_delay = 0.5

    def on_modified(self, event: FileSystemEvent) -> None:  # check_unused_code: ignore
        if event.is_directory:
            return

        # Only reload on Python file changes that affect worker functionality
        filepath = str(event.src_path)
        if self._should_reload_for_file(filepath):
            self._handle_reload(filepath)

    def _should_reload_for_file(self, filepath: str) -> bool:
        """Determine if file change should trigger worker reload"""
        if not filepath.endswith(".py"):
            return False

        # Always reload for worker.py itself
        if "worker.py" in filepath:
            return True

        # Skip files that definitely don't affect worker
        skip_patterns = [
            "/static/",
            "/dist/",
            "/templates/",
            "/scripts/generate_types.py",
            "/tests/",
            "test_",
            "_test.py",
            "__pycache__",
            ".pyc",
        ]

        for pattern in skip_patterns:
            if pattern in filepath:
                return False

        # Include worker-relevant files in app/ directory
        if "app/" in filepath:
            # Skip API routes - they don't affect background worker
            # Include everything else in app/ (core, workers, models, services, etc.)
            return "/app/routers/" not in filepath

        return False

    def _handle_reload(self, filepath: str) -> None:
        """Handle reload by signaling restart"""

        current_time = time.time()

        # Debounce: ignore if less than reload_delay seconds since last reload
        if current_time - self.last_reload_time < self.reload_delay:
            return

        self.last_reload_time = current_time

        logger.info(f"File changed: {filepath}")
        logger.info("Triggering worker restart...")

        # Record metric
        record_worker_restart(reason="file_change")

        # Signal restart via event
        self.restart_event.set()


# Configure logging, tracing, and error tracking
configure_logging(level=logging.DEBUG)
configure_tracing()
configure_sentry()
logger = logging.getLogger(__name__)

# Start metrics server on port 9092
start_metrics_server(9092, settings.environment)


async def run_worker_with_reload() -> None:
    """Run worker with automatic restart on file changes"""
    while True:
        restart_event = asyncio.Event()
        observer = None

        # Check if hot reload should be enabled
        reload_enabled = _should_enable_hot_reload()

        if reload_enabled:
            logger.info("Hot reload enabled - watching for file changes")

            # Set up file watcher
            event_handler = WorkerReloadHandler(restart_event)
            observer = Observer()

            # Watch the app directory and worker.py
            app_path = Path("app").resolve()
            if app_path.exists():
                observer.schedule(event_handler, str(app_path), recursive=True)

            worker_path = Path("worker.py").resolve()
            if worker_path.exists():
                observer.schedule(
                    event_handler, str(worker_path.parent), recursive=False
                )

            observer.start()
            logger.info(f"Watching for changes in: {app_path}, worker.py")
        else:
            logger.info("Hot reload disabled")

        # Create and start worker
        worker = create_queue_worker()

        try:
            if reload_enabled:
                # Run worker with restart monitoring
                worker_task = asyncio.create_task(worker.run())
                restart_task = asyncio.create_task(restart_event.wait())

                # Wait for either worker completion or restart signal
                _done, pending = await asyncio.wait(
                    [worker_task, restart_task], return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task  # type: ignore[async-error]
                    except asyncio.CancelledError:
                        pass

                # Check if we need to restart
                if restart_event.is_set():
                    logger.info("Restarting worker...")
                    worker.stop()
                    if observer:
                        observer.stop()
                        observer.join()
                    continue  # Restart the loop
                else:
                    # Worker completed normally
                    break
            else:
                # Run worker without reload
                await worker.run()
                break

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            break
        finally:
            worker.stop()
            if observer:
                observer.stop()
                observer.join()

        # If not reloading, break out of loop
        if not reload_enabled:
            break


if __name__ == "__main__":
    asyncio.run(run_worker_with_reload())
