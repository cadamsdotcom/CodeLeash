"""Field guard utility to prevent mass-assignment attacks in repository updates."""

from collections.abc import Set
from typing import Any


class ForbiddenFieldError(Exception):
    """Raised when update data contains fields not in the allowlist."""

    def __init__(self, forbidden: set[str], allowed: Set[str], table: str) -> None:
        self.forbidden = forbidden
        super().__init__(
            f"Forbidden fields in update to '{table}': {sorted(forbidden)}. "
            f"Allowed: {sorted(allowed)}"
        )


def enforce_allowed_fields(data: dict[str, Any], allowed: Set[str], table: str) -> None:
    """Raise ForbiddenFieldError if data contains keys outside allowed + auto-managed fields."""
    auto_managed = {"updated_at", "created_at"}
    forbidden = set(data.keys()) - allowed - auto_managed
    if forbidden:
        raise ForbiddenFieldError(forbidden, allowed, table)
