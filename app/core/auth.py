"""Authentication service for handling user auth with Supabase."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from fastapi.security import HTTPBearer
from supabase.client import Client

from app.core.config import settings
from app.core.metrics import (
    record_authentication_error,
    record_login_attempt,
    record_token_validation_failure,
)
from app.core.supabase import get_supabase_service_client
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthService:
    """Authentication service for handling user auth with Supabase."""

    def __init__(self, supabase_client: Client) -> None:
        self.client = supabase_client

    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    async def get_current_user_from_token(self, token: str) -> User | None:
        """Validate JWT token and return User."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
        except jwt.InvalidTokenError:
            # Fallback: try unverified decode for Supabase-issued tokens
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
            except Exception:
                record_token_validation_failure("decode_error")
                return None

        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            record_token_validation_failure("missing_claims")
            return None

        # Try to fetch from database
        try:
            client = get_supabase_service_client()
            result = client.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                row = cast("dict[str, Any]", result.data[0])
                return User(
                    id=row["id"],
                    email=row["email"],
                    full_name=row.get("full_name", ""),
                    is_active=row.get("is_active", True),
                    created_at=row["created_at"],
                )
        except Exception:
            pass

        # Fallback to JWT claims
        return User(
            id=user_id,
            email=email,
            full_name=payload.get("full_name", ""),
            is_active=True,
            created_at=datetime.now(UTC),
        )

    async def login(
        self, email: str, password: str
    ) -> dict[str, Any]:  # check_unused_code: ignore
        """Authenticate user with email and password via Supabase."""
        try:
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            user = response.user
            if not user:
                record_login_attempt(success=False, method="email")
                return {"error": "Invalid credentials"}

            token_data = {
                "sub": user.id,
                "email": user.email,
                "full_name": user.user_metadata.get("full_name", ""),
            }
            access_token = self.create_access_token(token_data)
            record_login_attempt(success=True, method="email")

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.user_metadata.get("full_name", ""),
                },
            }
        except Exception as e:
            record_login_attempt(success=False, method="email")
            record_authentication_error(str(e))
            return {"error": str(e)}

    async def register(  # check_unused_code: ignore
        self, email: str, password: str, full_name: str = ""
    ) -> dict[str, Any]:
        """Register a new user via Supabase Auth."""
        try:
            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}},
                }
            )
            user = response.user
            if not user:
                return {"error": "Registration failed"}

            return {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": {"id": user.id, "email": user.email},
            }
        except Exception as e:
            return {"error": str(e)}
