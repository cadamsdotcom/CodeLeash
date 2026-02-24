"""Index route serving the hello world page."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.service_dependencies import get_greeting_service
from app.core.templates import render_page

if TYPE_CHECKING:
    from app.services.greeting import GreetingService

router = APIRouter(tags=["index"])


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    greeting_service: GreetingService = Depends(get_greeting_service),
) -> HTMLResponse:
    greetings = await greeting_service.get_all()
    initial_data = {
        "greetings": [g.model_dump(mode="json") for g in greetings],
    }
    return render_page(
        request,
        "src/roots/index.tsx",
        title="CodeLeash",
        initial_data=initial_data,
    )
