"""Sample service demonstrating the service pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.greeting import Greeting

if TYPE_CHECKING:
    from app.repositories.greeting import GreetingRepository


class GreetingService:
    def __init__(self, greeting_repository: GreetingRepository) -> None:
        self.greeting_repository = greeting_repository

    async def get_all(self) -> list[Greeting]:
        data = await self.greeting_repository.get_all()
        return [Greeting(**row) for row in data]

    async def create(self, message: str) -> Greeting:
        data = await self.greeting_repository.create({"message": message})
        return Greeting(**data)
