"""Shared fixtures for integration tests"""

import os
from datetime import UTC, datetime

import pytest
from dotenv import load_dotenv
from supabase.client import Client

from app.models.user import User
from app.repositories.greeting import GreetingRepository
from app.services.greeting import GreetingService
from supabase import create_client  # type: ignore[attr-defined]

# Load environment variables from .env file
load_dotenv()


def _create_supabase_client() -> Client:
    """Helper to create a Supabase client with service role key."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        pytest.fail(
            "Supabase environment variables not configured. Ensure .env file exists with SUPABASE_URL and SUPABASE_SERVICE_KEY"
        )

    return create_client(url, key)


@pytest.fixture
def local_supabase_client() -> Client:
    """Create a Supabase client connected to local development instance."""
    return _create_supabase_client()


@pytest.fixture
def admin_client() -> Client:
    """Create a separate admin client for setup operations."""
    return _create_supabase_client()


@pytest.fixture
def greeting_repository(local_supabase_client: Client) -> GreetingRepository:
    """Create GreetingRepository instance for integration tests."""
    return GreetingRepository(local_supabase_client)


@pytest.fixture
def greeting_service(greeting_repository: GreetingRepository) -> GreetingService:
    """Create GreetingService instance for integration tests."""
    return GreetingService(greeting_repository=greeting_repository)


@pytest.fixture
def test_user() -> User:
    """Create a mock user for authenticated API tests."""
    return User(
        id="test-user-001",
        email="integration@example.com",
        full_name="Integration Test User",
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
