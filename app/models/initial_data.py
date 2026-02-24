"""Page-level initial data models for server-to-client data passing."""

from pydantic import BaseModel

from .greeting import Greeting


class IndexPageData(BaseModel):
    greetings: list[Greeting] = []
