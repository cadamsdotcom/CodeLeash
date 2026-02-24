"""Polling utilities for e2e tests.

This module provides polling utilities to wait for database state changes
instead of using time.sleep(). All e2e tests should use these utilities
to make tests faster and more reliable.
"""

import time
from collections.abc import Callable
from typing import Any

from tests.e2e.conftest import get_supabase_client


def poll_until(
    condition_fn: Callable[[], bool],
    timeout: float = 10.0,
    interval: float = 0.1,
    description: str = "condition",
) -> None:
    """Poll until a condition function returns True.

    Args:
        condition_fn: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds (default: 10)
        interval: Time between polls in seconds (default: 0.1)
        description: Human-readable description for error messages

    Raises:
        TimeoutError: If condition is not met within timeout period

    Example:
        poll_until(
            lambda: len(get_items()) > 0,
            timeout=5,
            description="items to appear"
        )
    """

    elapsed = 0.0
    while elapsed < timeout:
        if condition_fn():
            return
        time.sleep(interval)
        elapsed += interval

    raise TimeoutError(
        f"Timeout waiting for {description} after {timeout}s (polled every {interval}s)"
    )


def wait_for_db_record(
    table: str,
    filters: dict[str, Any],
    timeout: float = 10.0,
    description: str | None = None,
) -> dict[str, Any]:
    """Poll database until a record matching filters appears.

    Args:
        table: Database table name
        filters: Dict of field:value pairs to match (all must match)
        timeout: Maximum time to wait in seconds (default: 10)
        description: Human-readable description (auto-generated if None)

    Returns:
        The matching database record as a dict

    Raises:
        TimeoutError: If no matching record found within timeout

    Example:
        record = wait_for_db_record(
            "greetings",
            {"user_id": user_id, "message": "Hello world"},
            description="greeting from user"
        )
    """

    if description is None:
        filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items())
        description = f"{table} record where {filter_desc}"

    def check_record() -> dict[str, Any] | None:
        client = get_supabase_client()
        query = client.table(table).select("*")
        for field, value in filters.items():
            query = query.eq(field, value)
        response = query.execute()
        return response.data[0] if response.data else None

    record = None

    def condition() -> bool:
        nonlocal record
        record = check_record()
        return record is not None

    poll_until(condition, timeout=timeout, description=description)
    assert record is not None  # poll_until succeeded, so record must be set
    return record


def wait_for_db_records_count(
    table: str,
    filters: dict[str, Any],
    expected_count: int,
    timeout: float = 10.0,
    description: str | None = None,
) -> list[dict[str, Any]]:
    """Poll database until record count matches expected value.

    Args:
        table: Database table name
        filters: Dict of field:value pairs to match (all must match)
        expected_count: Expected number of matching records
        timeout: Maximum time to wait in seconds (default: 10)
        description: Human-readable description (auto-generated if None)

    Returns:
        List of matching database records

    Raises:
        TimeoutError: If count doesn't match within timeout

    Example:
        notifications = wait_for_db_records_count(
            "notifications",
            {"user_id": user_id, "is_read": False},
            expected_count=3,
            description="3 unread notifications"
        )
    """

    if description is None:
        filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items())
        description = f"{expected_count} {table} records where {filter_desc}"

    records = []

    def check_count() -> bool:
        nonlocal records
        client = get_supabase_client()
        query = client.table(table).select("*")
        for field, value in filters.items():
            query = query.eq(field, value)
        response = query.execute()
        records = response.data
        return len(records) == expected_count

    poll_until(check_count, timeout=timeout, description=description)
    return records
