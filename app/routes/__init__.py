"""Route registration for the FastAPI application."""

from fastapi import FastAPI

from app.routes import greetings_api, index, utils


def register_routes(app: FastAPI) -> None:
    """Register all application routes."""

    # Web routes
    app.include_router(index.router)
    app.include_router(utils.router)

    # API routes
    app.include_router(greetings_api.router)
