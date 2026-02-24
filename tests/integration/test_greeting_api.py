"""Integration tests for the greetings API with real Supabase."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_dependencies import get_current_user
from app.core.service_dependencies import get_greeting_service
from app.routes.greetings_api import router


@pytest.fixture
def api_client(
    test_user: Any, greeting_service: Any  # noqa: ANN401
) -> Generator[TestClient, None, None]:
    """Create a test client with auth overridden and real greeting service."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_greeting_service] = lambda: greeting_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestGreetingAPIIntegration:
    """Integration tests for the greetings API against real Supabase."""

    def test_create_and_list_greetings(self, api_client: TestClient) -> None:
        """Create a greeting via POST, then verify it appears in GET."""
        create_response = api_client.post(
            "/api/greetings", json={"message": "Integration test greeting"}
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["message"] == "Integration test greeting"
        assert "id" in created

        list_response = api_client.get("/api/greetings")
        assert list_response.status_code == 200
        greetings = list_response.json()
        assert any(g["id"] == created["id"] for g in greetings)
