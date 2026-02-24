"""Greeting model for the hello-world scaffold."""

from datetime import datetime

from pydantic import BaseModel


class Greeting(BaseModel):
    id: str
    message: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
