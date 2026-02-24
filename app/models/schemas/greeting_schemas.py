"""Request and response schemas for the greetings API."""

from pydantic import BaseModel


class CreateGreetingRequest(BaseModel):
    message: str


class GreetingResponse(BaseModel):
    id: str
    message: str
    created_at: str
    updated_at: str
