"""Unit tests for GreetingService."""

from typing import Any

import pytest

from app.models.greeting import Greeting
from app.services.greeting import GreetingService


class TestGreetingService:
    """Tests for GreetingService.get_all()."""

    @pytest.fixture
    def mock_repository(self) -> type:
        """Create a mock repository with predefined responses."""

        class MockGreetingRepository:
            def __init__(self, data: list[dict[str, Any]]) -> None:
                self._data = data
                self.created: dict[str, Any] | None = None

            async def get_all(self) -> list[dict[str, Any]]:
                return self._data

            async def create(self, data: dict[str, Any]) -> dict[str, Any]:
                self.created = data
                return {
                    "id": "greeting-new",
                    "message": data["message"],
                    "created_at": "2026-01-15T00:00:00Z",
                    "updated_at": "2026-01-15T00:00:00Z",
                    "deleted_at": None,
                }

        return MockGreetingRepository

    @pytest.mark.asyncio
    async def test_get_all_returns_greetings(self, mock_repository: type) -> None:
        """Test that get_all returns a list of Greeting models."""
        raw_data = [
            {
                "id": "greeting-001",
                "message": "Hello from CodeLeash!",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "deleted_at": None,
            },
            {
                "id": "greeting-002",
                "message": "Welcome!",
                "created_at": "2026-01-02T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "deleted_at": None,
            },
        ]
        repo = mock_repository(raw_data)
        service = GreetingService(greeting_repository=repo)

        result = await service.get_all()

        assert len(result) == 2
        assert all(isinstance(g, Greeting) for g in result)
        assert result[0].message == "Hello from CodeLeash!"
        assert result[1].message == "Welcome!"

    @pytest.mark.asyncio
    async def test_get_all_returns_empty_list(self, mock_repository: type) -> None:
        """Test that get_all returns empty list when no greetings exist."""
        repo = mock_repository([])
        service = GreetingService(greeting_repository=repo)

        result = await service.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_create_greeting(self, mock_repository: type) -> None:
        """Test that create() calls repository and returns a Greeting model."""
        repo = mock_repository([])
        service = GreetingService(greeting_repository=repo)

        result = await service.create("Hello, TDD!")

        assert isinstance(result, Greeting)
        assert result.id == "greeting-new"
        assert result.message == "Hello, TDD!"
        assert repo.created == {"message": "Hello, TDD!"}
