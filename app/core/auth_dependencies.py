"""Authentication dependency functions for FastAPI route dependencies."""

from datetime import UTC, datetime
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.container import _get_container
from app.models.user import User

security = HTTPBearer()


def _decode_token_with_fallback(token: str) -> dict[str, Any] | None:
    """Decode JWT token, falling back to unverified decode for Supabase tokens."""
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.InvalidTokenError:
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None


async def get_current_user_from_cookie(request: Request) -> User | None:
    """Get current user from JWT cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = _decode_token_with_fallback(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        return None

    return User(
        id=user_id,
        email=email,
        full_name=payload.get("full_name", ""),
        is_active=True,
        created_at=datetime.now(UTC),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dependency to get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        container = _get_container()
        service = container.get_auth_service()
        user = await service.get_current_user_from_token(token)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """Optional dependency to get current user (returns None if not authenticated)."""
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        container = _get_container()
        service = container.get_auth_service()
        return await service.get_current_user_from_token(token)
    except Exception:
        return None


async def get_current_user_flexible(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> User:
    """Get current user from either cookie or bearer token."""
    user = await get_current_user_from_cookie(request)
    if user:
        return user

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        container = _get_container()
        service = container.get_auth_service()
        user = await service.get_current_user_from_token(token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
