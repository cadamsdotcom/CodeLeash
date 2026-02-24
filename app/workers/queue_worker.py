"""Generic queue worker for processing background jobs."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from app.core.metrics import record_queue_job_duration, record_queue_job_processed

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.repositories.job import Job, JobRepository

logger = logging.getLogger(__name__)


class QueueWorker:
    """Processes jobs from registered queue handlers.

    Args:
        job_repo: JobRepository instance for claiming/completing jobs
        handlers: Dict mapping queue names to handler callables (async handle(job) methods)
    """

    def __init__(self, job_repo: JobRepository, handlers: dict[str, Any]) -> None:
        self.job_repo = job_repo
        self.handlers = handlers
        self._running = False
        self._active_tasks: set[asyncio.Task[None]] = set()

    async def run(self, poll_interval: float = 5) -> None:
        """Main polling loop. Claims and processes jobs until stopped."""
        self._running = True
        queues = list(self.handlers.keys())
        logger.info(f"Queue worker started, polling queues: {queues}")

        while self._running:
            try:
                jobs = await self.job_repo.claim(queues=queues, limit=1)
                for job in jobs:
                    task: asyncio.Task[None] = asyncio.create_task(
                        self._execute_job(job)
                    )
                    self._active_tasks.add(task)
                    task.add_done_callback(self._active_tasks.discard)
            except Exception:
                logger.exception("Error claiming jobs")

            await asyncio.sleep(poll_interval)

        logger.info("Queue worker stopped")

    async def _execute_job(self, job: Job) -> None:
        """Dispatch a job to its handler, then complete or fail it."""
        handler = self.handlers.get(job.queue)
        if handler is None:
            logger.error(f"No handler registered for queue {job.queue}")
            await self.job_repo.fail(job.id, f"No handler for queue {job.queue}")
            return

        start_time = time.time()
        try:
            handle_fn: Callable[..., Any] = handler.handle
            await handle_fn(job)
            await self.job_repo.complete(job.id)
            record_queue_job_processed(queue=job.queue, status="completed")
        except Exception as e:
            logger.exception(f"Error processing job {job.id} from queue {job.queue}")
            await self.job_repo.fail(job.id, str(e))
            record_queue_job_processed(queue=job.queue, status="failed")
        finally:
            duration = time.time() - start_time
            record_queue_job_duration(queue=job.queue, duration=duration)

    def stop(self) -> None:
        """Signal the worker to stop after the current poll cycle."""
        self._running = False

    async def stop_gracefully(
        self, timeout: float = 30
    ) -> None:  # check_unused_code: ignore
        """Stop the worker and wait for active tasks to complete."""
        self._running = False
        if self._active_tasks:
            logger.info(
                f"Waiting for {len(self._active_tasks)} active tasks to complete..."
            )
            _done, pending = await asyncio.wait(self._active_tasks, timeout=timeout)
            if pending:
                logger.warning(
                    f"Timed out waiting for {len(pending)} tasks, cancelling..."
                )
                for task in pending:
                    task.cancel()
