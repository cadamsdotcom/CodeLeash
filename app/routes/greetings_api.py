"""API routes for greetings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status

from app.core.auth_dependencies import get_current_user
from app.core.exceptions import handle_service_exception
from app.core.service_dependencies import get_greeting_service
from app.models.schemas.greeting_schemas import CreateGreetingRequest, GreetingResponse

if TYPE_CHECKING:
    from app.models.user import User
    from app.services.greeting import GreetingService

router = APIRouter(prefix="/api/greetings", tags=["greetings"])


@router.get("/", response_model=list[GreetingResponse])
async def list_greetings(
    _user: User = Depends(get_current_user),
    service: GreetingService = Depends(get_greeting_service),
) -> list[GreetingResponse]:
    """List all greetings."""
    try:
        greetings = await service.get_all()
        return [
            GreetingResponse(
                id=g.id,
                message=g.message,
                created_at=str(g.created_at),
                updated_at=str(g.updated_at),
            )
            for g in greetings
        ]
    except Exception as e:
        raise handle_service_exception(e)


@router.post("/", response_model=GreetingResponse, status_code=status.HTTP_201_CREATED)
async def create_greeting(
    body: CreateGreetingRequest,
    _user: User = Depends(get_current_user),
    service: GreetingService = Depends(get_greeting_service),
) -> GreetingResponse:
    """Create a new greeting."""
    try:
        greeting = await service.create(body.message)
        return GreetingResponse(
            id=greeting.id,
            message=greeting.message,
            created_at=str(greeting.created_at),
            updated_at=str(greeting.updated_at),
        )
    except Exception as e:
        raise handle_service_exception(e)
