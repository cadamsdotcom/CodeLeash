"""Integration tests for GreetingRepository against local Supabase."""

import pytest

from app.repositories.greeting import GreetingRepository


class TestGreetingRepository:
    """Tests for GreetingRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_all_returns_seeded_greeting(
        self, greeting_repository: GreetingRepository
    ) -> None:
        """Test that get_all returns the seeded greeting from the migration."""
        results = await greeting_repository.get_all()

        assert len(results) >= 1
        messages = [r["message"] for r in results]
        assert "Hello from CodeLeash!" in messages

    @pytest.mark.asyncio
    async def test_create_and_soft_delete(
        self, greeting_repository: GreetingRepository
    ) -> None:
        """Test creating a greeting and soft-deleting it."""
        # Create
        created = await greeting_repository.create(
            {"message": "Test greeting for integration"}
        )
        assert created["message"] == "Test greeting for integration"
        greeting_id = created["id"]

        # Verify it exists
        fetched = await greeting_repository.get_by_id(greeting_id)
        assert fetched is not None
        assert fetched["message"] == "Test greeting for integration"

        # Soft delete
        await greeting_repository.delete(greeting_id)

        # Verify it's soft-deleted (get_all should not return it)
        all_greetings = await greeting_repository.get_all()
        active_ids = [g["id"] for g in all_greetings]
        assert greeting_id not in active_ids
