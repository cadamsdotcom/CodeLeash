"""Custom exception handlers for the application."""

import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from jinja2 import TemplateError, TemplateNotFound, UndefinedError


async def template_error_handler(request: Request, exc: TemplateError) -> JSONResponse:
    """Handle Jinja2 template errors with detailed error messages."""
    show_details = os.getenv("ENVIRONMENT", "development").lower() == "development"

    if show_details:
        error_message = str(exc)
        error_type = type(exc).__name__

        return JSONResponse(
            status_code=500,
            content={
                "error": "Template Error",
                "type": error_type,
                "message": error_message,
                "detail": f"Jinja2 {error_type}: {error_message}",
                "path": str(request.url),
            },
        )
    else:
        return JSONResponse(
            status_code=500, content={"error": "Template rendering failed"}
        )


async def template_not_found_handler(
    request: Request, exc: TemplateNotFound
) -> JSONResponse:
    """Handle missing template errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Template Not Found",
            "message": f"Template '{exc.name}' not found",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


async def undefined_error_handler(
    request: Request, exc: UndefinedError
) -> JSONResponse:
    """Handle undefined variable errors in templates."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Undefined Variable",
            "message": str(exc),
            "detail": f"A variable used in the template is not defined: {exc}",
            "path": str(request.url),
        },
    )


class AppException(Exception):
    """Base exception class for the application."""

    pass


class NotFoundError(AppException):
    """Resource not found."""

    pass


class PermissionDeniedError(AppException):
    """Permission denied."""

    pass


class ValidationError(AppException):
    """Validation error."""

    pass


class BusinessLogicError(AppException):
    """Business logic error."""

    pass


def handle_service_exception(e: Exception) -> HTTPException:
    """Convert service exceptions to HTTP exceptions."""
    if isinstance(e, HTTPException):
        return e
    elif isinstance(e, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif isinstance(e, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    elif isinstance(e, ValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif isinstance(e, BusinessLogicError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e!s}",
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom exceptions and convert to HTTP responses."""
    http_exc = handle_service_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers with the FastAPI app."""
    app.exception_handler(TemplateError)(template_error_handler)
    app.exception_handler(TemplateNotFound)(template_not_found_handler)
    app.exception_handler(UndefinedError)(undefined_error_handler)
    app.exception_handler(AppException)(app_exception_handler)
