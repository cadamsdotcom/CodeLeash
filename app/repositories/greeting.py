"""Sample repository demonstrating the repository pattern."""

from supabase.client import Client

from app.repositories.base import BaseRepository


class GreetingRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__("greetings", client, supports_soft_delete=True)
