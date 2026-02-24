"""Simple job queue repository using native PostgreSQL with FOR UPDATE SKIP LOCKED."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from postgrest.types import CountMethod
from supabase.client import Client

from app.core.metrics import record_database_connection_error, update_queue_depth_gauge

logger = logging.getLogger(__name__)


@dataclass
class Job:
    """Represents a claimed job from the queue."""

    id: int
    queue: str
    payload: dict[str, Any]
    attempts: int
    max_attempts: int


class JobRepository:
    """Repository for simple PostgreSQL-based job queue operations.

    Uses direct table operations for most operations, except claim() which
    requires RPC for atomic FOR UPDATE SKIP LOCKED.
    """

    def __init__(self, client: Client) -> None:
        self.client = client
        self.table_name = "jobs"

    def _check_and_record_connection_error(self, exception: Exception) -> None:
        """Check if exception is a connection error and record metric."""
        error_str = str(exception).lower()
        if any(
            keyword in error_str
            for keyword in [
                "connection",
                "timeout",
                "network",
                "refused",
                "unreachable",
            ]
        ):
            record_database_connection_error()

    async def enqueue(  # check_unused_code: ignore
        self,
        queue: str,
        payload: dict[str, Any],
        delay_seconds: int = 0,
        max_attempts: int = 3,
    ) -> int:
        """Enqueue a new job.

        Args:
            queue: Job type/queue name (e.g. 'greeting-jobs')
            payload: Job data as JSON-serializable dict
            delay_seconds: Delay before job becomes available (default 0)
            max_attempts: Maximum retry attempts (default 3)

        Returns:
            Job ID
        """
        try:
            scheduled_for = datetime.now(UTC) + timedelta(seconds=delay_seconds)
            response = (
                self.client.table(self.table_name)
                .insert(
                    {
                        "queue": queue,
                        "payload": payload,
                        "scheduled_for": scheduled_for.isoformat(),
                        "max_attempts": max_attempts,
                    }
                )
                .execute()
            )

            if not response.data:
                raise Exception("Failed to enqueue job - no data returned")

            job_id = cast("dict[str, Any]", response.data[0])["id"]
            logger.debug(f"Enqueued job {job_id} to queue {queue}")

            # Update queue depth metric
            self._update_queue_depth_metric(queue)

            return job_id
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error enqueuing job to {queue}: {e!s}")

    async def claim(self, queues: list[str] | None = None, limit: int = 1) -> list[Job]:
        """Claim jobs atomically using FOR UPDATE SKIP LOCKED.

        Args:
            queues: List of queue names to claim from, or None for all queues
            limit: Maximum number of jobs to claim (default 1)

        Returns:
            List of claimed Job objects
        """
        try:
            response = self.client.rpc(
                "claim_jobs", {"p_queues": queues, "p_limit": limit}
            ).execute()

            jobs = []
            for row in cast("list[dict[str, Any]]", response.data or []):
                jobs.append(
                    Job(
                        id=row["id"],
                        queue=row["queue"],
                        payload=row["payload"],
                        attempts=row["attempts"],
                        max_attempts=row["max_attempts"],
                    )
                )

            if jobs:
                logger.debug(f"Claimed {len(jobs)} job(s) from queues {queues}")

            return jobs
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error claiming jobs from {queues}: {e!s}")

    async def complete(self, job_id: int) -> bool:
        """Mark a job as completed.

        Args:
            job_id: ID of the job to complete

        Returns:
            True if job was marked complete, False if not found or wrong status
        """
        try:
            response = (
                self.client.table(self.table_name)
                .update(
                    {
                        "status": "completed",
                        "completed_at": datetime.now(UTC).isoformat(),
                    }
                )
                .eq("id", job_id)
                .eq("status", "processing")
                .execute()
            )

            success = len(response.data) > 0
            if success:
                logger.debug(f"Completed job {job_id}")
            else:
                logger.warning(
                    f"Failed to complete job {job_id} - not found or wrong status"
                )

            return success
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error completing job {job_id}: {e!s}")

    async def fail(self, job_id: int, error: str | None = None) -> bool:
        """Mark a job as failed or schedule for retry.

        If attempts < max_attempts, schedules retry with exponential backoff.
        Otherwise marks as permanently failed.

        Args:
            job_id: ID of the job that failed
            error: Error message to store (optional)

        Returns:
            True if job status was updated
        """
        try:
            # First get job to check attempts
            job_resp = (
                self.client.table(self.table_name)
                .select("attempts, max_attempts, queue")
                .eq("id", job_id)
                .execute()
            )

            if not job_resp.data:
                logger.warning(f"Failed to fail job {job_id} - not found")
                return False

            job = cast("dict[str, Any]", job_resp.data[0])
            attempts: int = job["attempts"]
            max_attempts: int = job["max_attempts"]
            queue: str = job["queue"]

            if attempts >= max_attempts:
                # Permanently failed
                update_data = {
                    "status": "failed",
                    "last_error": error,
                    "completed_at": datetime.now(UTC).isoformat(),
                }
                logger.info(
                    f"Job {job_id} permanently failed after {attempts} attempts: {error}"
                )
            else:
                # Retry with exponential backoff (30s * attempt_number)
                backoff = timedelta(seconds=30 * attempts)
                scheduled_for = datetime.now(UTC) + backoff
                update_data = {
                    "status": "pending",
                    "last_error": error,
                    "scheduled_for": scheduled_for.isoformat(),
                }
                logger.info(
                    f"Job {job_id} scheduled for retry (attempt {attempts}/{max_attempts}) "
                    f"at {scheduled_for.isoformat()}: {error}"
                )

            response = (
                self.client.table(self.table_name)
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )

            success = len(response.data) > 0

            # Update queue depth metric
            self._update_queue_depth_metric(queue)

            return success
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error failing job {job_id}: {e!s}")

    async def get_queue_depth(self, queue: str | None = None) -> int:
        """Get count of pending jobs.

        Args:
            queue: Optional queue name to filter by

        Returns:
            Number of pending jobs
        """
        try:
            query = (
                self.client.table(self.table_name)
                .select("id", count=CountMethod.exact)
                .eq("status", "pending")
            )
            if queue:
                query = query.eq("queue", queue)

            response = query.execute()
            return response.count or 0
        except Exception as e:
            self._check_and_record_connection_error(e)
            logger.error(f"Error getting queue depth: {e!s}")
            return 0

    async def get_job_by_id(self, job_id: int) -> dict[str, Any] | None:
        """Get a job by its ID.

        Args:
            job_id: ID of the job to retrieve

        Returns:
            Job data as dict, or None if not found
        """
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", job_id)
                .execute()
            )

            if not response.data:
                return None

            return cast("dict[str, Any]", response.data[0])
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error getting job {job_id}: {e!s}")

    def _update_queue_depth_metric(self, queue: str) -> None:
        """Update queue depth metric (fire and forget)."""
        try:
            # Use synchronous count for simplicity in metric updates
            response = (
                self.client.table(self.table_name)
                .select("id", count=CountMethod.exact)
                .eq("status", "pending")
                .eq("queue", queue)
                .execute()
            )
            depth = response.count or 0
            update_queue_depth_gauge(queue_name=queue, depth=depth)
        except Exception:
            # Silently ignore metrics errors
            pass
