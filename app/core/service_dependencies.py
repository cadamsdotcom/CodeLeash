"""Service-only dependency injection functions.

This module should be imported by routes and services.
Repository dependency functions are NOT available here - they are in repository_dependencies.py
which is forbidden for routes and services by import-linter.
"""

from fastapi import Depends

from app.core.container import Container, _get_container
from app.services.greeting import GreetingService


def get_greeting_service(
    container: Container = Depends(_get_container),
) -> GreetingService:
    """Get GreetingService instance."""
    return container.get_greeting_service()
