"""Factory function for creating the queue worker with all dependencies."""

from app.core.container import _get_container
from app.workers.handlers.greeting_handler import GreetingHandler
from app.workers.queue_worker import QueueWorker


def create_queue_worker() -> QueueWorker:
    """Create a QueueWorker with all handlers wired up."""
    container = _get_container()

    greeting_handler = GreetingHandler(
        greeting_repository=container.get_greeting_repository()
    )

    return QueueWorker(
        job_repo=container.get_job_repository(),
        handlers={
            "greeting-jobs": greeting_handler,
        },
    )
