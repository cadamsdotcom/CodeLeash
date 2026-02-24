"""Unit tests for the greetings API route."""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_dependencies import get_current_user
from app.core.service_dependencies import get_greeting_service
from app.models.greeting import Greeting
from app.models.user import User
from app.routes.greetings_api import router


def _make_greeting(id: str, message: str) -> Greeting:
    return Greeting(
        id=id,
        message=message,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _make_test_user() -> User:
    return User(
        id="user-001",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestGreetingsAPI:
    """Tests for the greetings API endpoints."""

    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def authenticated_client(self, app: FastAPI) -> Generator[TestClient, None, None]:
        user = _make_test_user()
        app.dependency_overrides[get_current_user] = lambda: user
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def unauthenticated_client(self, app: FastAPI) -> TestClient:
        return TestClient(app)

    def test_list_greetings_returns_all(
        self, app: FastAPI, authenticated_client: TestClient
    ) -> None:
        greetings = [
            _make_greeting("g-1", "Hello"),
            _make_greeting("g-2", "World"),
        ]

        class MockService:
            async def get_all(self) -> list[Greeting]:
                return greetings

        app.dependency_overrides[get_greeting_service] = lambda: MockService()

        response = authenticated_client.get("/api/greetings")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "g-1"
        assert data[0]["message"] == "Hello"
        assert data[1]["id"] == "g-2"
        assert data[1]["message"] == "World"

    def test_create_greeting_returns_created(
        self, app: FastAPI, authenticated_client: TestClient
    ) -> None:
        created = _make_greeting("g-new", "New greeting")

        class MockService:
            async def create(self, message: str) -> Greeting:
                return created

        app.dependency_overrides[get_greeting_service] = lambda: MockService()

        response = authenticated_client.post(
            "/api/greetings", json={"message": "New greeting"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "g-new"
        assert data["message"] == "New greeting"

    def test_list_greetings_unauthenticated_returns_401(
        self, unauthenticated_client: TestClient
    ) -> None:
        response = unauthenticated_client.get("/api/greetings")
        assert response.status_code == 403
