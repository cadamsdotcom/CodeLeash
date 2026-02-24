"""Tests for the queue worker."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.job import Job
from app.workers.queue_worker import QueueWorker


class TestQueueWorker:
    @pytest.fixture()
    def job_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.claim = AsyncMock(return_value=[])
        repo.complete = AsyncMock(return_value=True)
        repo.fail = AsyncMock(return_value=True)
        return repo

    @pytest.fixture()
    def handler(self) -> MagicMock:
        handler = MagicMock()
        handler.handle = AsyncMock(return_value={"status": "ok"})
        return handler

    @pytest.fixture()
    def worker(self, job_repo: MagicMock, handler: MagicMock) -> QueueWorker:
        return QueueWorker(job_repo=job_repo, handlers={"greeting-jobs": handler})

    @pytest.fixture()
    def job(self) -> Job:
        return Job(
            id=1,
            queue="greeting-jobs",
            payload={"greeting_id": 42},
            attempts=1,
            max_attempts=3,
        )

    @pytest.mark.asyncio()
    async def test_execute_job_dispatches_to_handler(
        self, worker: QueueWorker, handler: MagicMock, job: Job
    ) -> None:
        await worker._execute_job(job)

        handler.handle.assert_called_once_with(job)

    @pytest.mark.asyncio()
    async def test_execute_job_marks_complete_on_success(
        self, worker: QueueWorker, job_repo: MagicMock, handler: MagicMock, job: Job
    ) -> None:
        await worker._execute_job(job)

        job_repo.complete.assert_called_once_with(job.id)

    @pytest.mark.asyncio()
    async def test_execute_job_marks_failed_on_handler_error(
        self, worker: QueueWorker, job_repo: MagicMock, handler: MagicMock, job: Job
    ) -> None:
        handler.handle.side_effect = Exception("handler exploded")

        await worker._execute_job(job)

        job_repo.fail.assert_called_once_with(job.id, "handler exploded")
