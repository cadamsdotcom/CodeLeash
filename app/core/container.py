"""Dependency injection container for services and repositories."""

from functools import lru_cache
from typing import Any

from supabase.client import Client

from app.core.auth import AuthService
from app.core.supabase import get_supabase_client, get_supabase_service_client
from app.repositories.greeting import GreetingRepository
from app.repositories.job import JobRepository
from app.services.greeting import GreetingService


class Container:
    """Dependency injection container."""

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}
        self._supabase_client: Client | None = None

    def get_supabase_service_client(self) -> Client:
        """Get Supabase service client instance for backend operations."""
        if self._supabase_client is None:
            self._supabase_client = get_supabase_service_client()
        return self._supabase_client

    def get_greeting_repository(self) -> GreetingRepository:
        """Get GreetingRepository instance."""
        if "greeting_repository" not in self._instances:
            self._instances["greeting_repository"] = GreetingRepository(
                self.get_supabase_service_client()
            )
        return self._instances["greeting_repository"]

    def get_greeting_service(self) -> GreetingService:
        """Get GreetingService instance."""
        if "greeting_service" not in self._instances:
            self._instances["greeting_service"] = GreetingService(
                greeting_repository=self.get_greeting_repository()
            )
        return self._instances["greeting_service"]

    def get_job_repository(self) -> JobRepository:
        """Get JobRepository instance."""
        if "job_repository" not in self._instances:
            self._instances["job_repository"] = JobRepository(
                self.get_supabase_service_client()
            )
        return self._instances["job_repository"]

    def get_auth_service(self) -> AuthService:
        """Get AuthService instance."""
        if "auth_service" not in self._instances:
            self._instances["auth_service"] = AuthService(
                supabase_client=get_supabase_client()
            )
        return self._instances["auth_service"]


@lru_cache
def _get_container() -> Container:
    """Get the application container instance (internal use only)."""
    return Container()
