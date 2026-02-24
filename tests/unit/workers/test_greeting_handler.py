"""Tests for the greeting handler."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.job import Job
from app.workers.handlers.greeting_handler import GreetingHandler


class TestGreetingHandler:
    @pytest.fixture()
    def greeting_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        return repo

    @pytest.fixture()
    def handler(self, greeting_repo: MagicMock) -> GreetingHandler:
        return GreetingHandler(greeting_repository=greeting_repo)

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
    async def test_handle_processes_greeting_job(
        self, handler: GreetingHandler, greeting_repo: MagicMock, job: Job
    ) -> None:
        greeting_repo.get_by_id.return_value = {"id": 42, "message": "Hello!"}

        result = await handler.handle(job)

        greeting_repo.get_by_id.assert_called_once_with(42)
        assert result["status"] == "processed"
        assert result["greeting_id"] == 42

    @pytest.mark.asyncio()
    async def test_handle_missing_greeting(
        self, handler: GreetingHandler, greeting_repo: MagicMock, job: Job
    ) -> None:
        greeting_repo.get_by_id.return_value = None

        result = await handler.handle(job)

        assert result["status"] == "not_found"
        assert result["greeting_id"] == 42
