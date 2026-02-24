"""
Database error handling utilities for PostgreSQL/Supabase errors.
Provides user-friendly error messages based on specific constraint violations.
"""

from typing import Any

from app.core.metrics import record_database_error


def parse_db_error(error: Exception) -> dict[str, Any]:
    """
    Parse a database error and extract relevant information.

    Returns a dict with:
    - code: PostgreSQL error code
    - constraint: The constraint that was violated
    - message: The original error message
    - user_message: A user-friendly error message
    """
    error_str = str(error)
    result = {
        "code": None,
        "constraint": None,
        "message": error_str,
        "user_message": "A database error occurred",
    }

    # Try to extract error details from the error string
    if "'code':" in error_str:
        if "'code': '23505'" in error_str or '"code": "23505"' in error_str:
            result["code"] = "23505"  # Unique constraint violation
        elif "'code': '23503'" in error_str or '"code": "23503"' in error_str:
            result["code"] = "23503"  # Foreign key violation
        elif "'code': '23502'" in error_str or '"code": "23502"' in error_str:
            result["code"] = "23502"  # Not null violation
        elif "'code': '23514'" in error_str or '"code": "23514"' in error_str:
            result["code"] = "23514"  # Check constraint violation
        elif "'code': 'P0001'" in error_str or '"code": "P0001"' in error_str:
            result["code"] = "P0001"  # Raise exception from function/trigger

    # Generate user-friendly message based on code
    if result["code"] == "23505":  # Unique constraint violation
        if "email" in error_str.lower():
            error_category = "duplicate_email"
            result["user_message"] = "An account with this email already exists"
        else:
            error_category = "duplicate_record"
            result["user_message"] = "This record already exists"

        record_database_error(
            error_code="23505",
            constraint=result["constraint"] or "",
            constraint_type="unique",
            error_category=error_category,
        )

    elif result["code"] == "23503":  # Foreign key violation
        error_category = "missing_reference"
        result["user_message"] = "Referenced record does not exist"
        record_database_error(
            error_code="23503",
            constraint=result["constraint"] or "",
            constraint_type="foreign_key",
            error_category=error_category,
        )

    elif result["code"] == "23502":  # Not null violation
        record_database_error(
            error_code="23502",
            constraint=result["constraint"] or "",
            constraint_type="not_null",
            error_category="missing_field",
        )
        result["user_message"] = "Required field is missing"

    elif result["code"] == "23514":  # Check constraint violation
        error_category = "check_constraint"
        result["user_message"] = result["message"]
        record_database_error(
            error_code="23514",
            constraint=result["constraint"] or "",
            constraint_type="check",
            error_category=error_category,
        )

    elif result["code"] == "P0001":  # Raise exception from function/trigger
        error_category = "custom_error"
        result["user_message"] = result["message"]
        record_database_error(
            error_code="P0001",
            constraint=result["constraint"] or "",
            constraint_type="",
            error_category=error_category,
        )

    # Fallback checks for common error patterns
    elif "duplicate key value" in error_str.lower():
        if "email" in error_str.lower():
            error_category = "duplicate_email"
            result["user_message"] = "An account with this email already exists"
        else:
            error_category = "duplicate_record"
            result["user_message"] = "This record already exists"

        record_database_error(
            error_code="",
            constraint="",
            constraint_type="unique",
            error_category=error_category,
        )
    elif "foreign key constraint" in error_str.lower():
        record_database_error(
            error_code="",
            constraint="",
            constraint_type="foreign_key",
            error_category="missing_reference",
        )
        result["user_message"] = "Referenced record does not exist or is invalid"

    return result


class DatabaseError(Exception):
    """Custom exception for database errors with user-friendly messages."""

    def __init__(
        self, message: str, code: str | None = None, constraint: str | None = None
    ) -> None:
        self.message = message
        self.code = code
        self.constraint = constraint
        super().__init__(message)


def handle_db_error(error: Exception) -> DatabaseError:
    """Convert a raw database exception into a DatabaseError with a user-friendly message."""
    error_info = parse_db_error(error)
    return DatabaseError(
        message=error_info["user_message"],
        code=error_info["code"],
        constraint=error_info["constraint"],
    )
