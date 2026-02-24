"""Repository-only dependency injection functions.

This module should ONLY be imported by repositories.
Services and routes are forbidden from importing this module by import-linter.
"""

from fastapi import Depends

from app.core.container import Container, _get_container
from app.repositories.greeting import GreetingRepository


def get_greeting_repository(
    container: Container = Depends(_get_container),
) -> GreetingRepository:
    """Get GreetingRepository instance."""
    return container.get_greeting_repository()
