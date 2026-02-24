"""Base repository class with common CRUD operations"""

import logging
import uuid
from abc import ABC
from datetime import UTC, datetime
from typing import Any, cast

from postgrest.types import CountMethod
from supabase.client import Client

from app.core.db_errors import handle_db_error
from app.core.field_guard import enforce_allowed_fields
from app.core.metrics import record_database_connection_error


class BaseRepository(ABC):
    """Base repository class with common database operations"""

    ALLOWED_UPDATE_FIELDS: frozenset[str] | None = None

    def __init__(
        self, table_name: str, client: Client, supports_soft_delete: bool = False
    ) -> None:
        self.table_name = table_name
        self.client = client
        self.supports_soft_delete = supports_soft_delete

    def _check_and_record_connection_error(self, exception: Exception) -> None:
        """Check if exception is a connection error and record metric"""
        error_str = str(exception).lower()
        if any(
            keyword in error_str
            for keyword in [
                "connection",
                "timeout",
                "network",
                "refused",
                "unreachable",
            ]
        ):
            record_database_connection_error()

    async def get_by_id(
        self, id: str, include_deleted: bool = False
    ) -> dict[str, Any] | None:
        """Get a record by ID, excluding soft-deleted by default if supported"""
        try:
            query = self.client.table(self.table_name).select("*").eq("id", id)
            if self.supports_soft_delete and not include_deleted:
                query = query.is_("deleted_at", "null")
            response = query.execute()
            return cast("dict[str, Any]", response.data[0]) if response.data else None
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error getting {self.table_name} by id {id}: {e!s}")

    async def get_all(
        self, limit: int | None = None, offset: int = 0, include_deleted: bool = False
    ) -> list[dict[str, Any]]:
        """Get all records with optional pagination, excluding soft-deleted by default if supported"""
        try:
            query = self.client.table(self.table_name).select("*")
            if self.supports_soft_delete and not include_deleted:
                query = query.is_("deleted_at", "null")
            if limit:
                query = query.limit(limit).offset(offset)
            response = query.execute()
            return cast("list[dict[str, Any]]", response.data or [])
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error getting all {self.table_name}: {e!s}")

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record"""
        try:
            # Generate UUID if not provided
            if "id" not in data:
                data["id"] = str(uuid.uuid4())

            # Add timestamps
            now = datetime.now(UTC).isoformat()
            data.update({"created_at": now, "updated_at": now})

            response = self.client.table(self.table_name).insert(data).execute()
            if not response.data:
                raise Exception(f"Failed to create {self.table_name}")
            # Return the data we know was inserted (including the generated ID)
            return data
        except Exception as e:
            # Check for connection errors
            self._check_and_record_connection_error(e)

            # Log the original error for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"Database error creating {self.table_name}: {e}")
            logger.error(f"Data that failed: {data}")

            # Use the error handler to get a user-friendly message
            db_error = handle_db_error(e)
            raise db_error

    async def update(self, id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a record by ID"""
        if self.ALLOWED_UPDATE_FIELDS is not None:
            enforce_allowed_fields(data, self.ALLOWED_UPDATE_FIELDS, self.table_name)
        try:
            # Add updated timestamp
            data["updated_at"] = datetime.now(UTC).isoformat()

            response = (
                self.client.table(self.table_name).update(data).eq("id", id).execute()
            )
            return cast("dict[str, Any]", response.data[0]) if response.data else None
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error updating {self.table_name} {id}: {e!s}")

    async def delete(self, id: str) -> bool:
        """Delete a record - soft delete if supported, otherwise hard delete"""
        try:
            if self.supports_soft_delete:
                # Soft delete: set deleted_at timestamp
                data = {"deleted_at": datetime.now(UTC).isoformat()}
                result = await self.update(id, data)
                return result is not None
            else:
                # Hard delete: remove from database
                self.client.table(self.table_name).delete().eq("id", id).execute()
                return True
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error deleting {self.table_name} {id}: {e!s}")

    async def find_by_field(  # check_unused_code: ignore
        self, field: str, value: Any, include_deleted: bool = False  # noqa: ANN401
    ) -> list[dict[str, Any]]:
        """Find records by a specific field value, excluding soft-deleted by default if supported"""
        try:
            query = self.client.table(self.table_name).select("*").eq(field, value)
            if self.supports_soft_delete and not include_deleted:
                query = query.is_("deleted_at", "null")
            response = query.execute()
            return cast("list[dict[str, Any]]", response.data or [])
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(
                f"Error finding {self.table_name} by {field}={value}: {e!s}"
            )

    async def count(self) -> int:
        """Count total records"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("id", count=CountMethod.exact)
                .execute()
            )
            return response.count or 0
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(f"Error counting {self.table_name}: {e!s}")

    async def get_by_fields(
        self,
        filters: dict[str, Any],
        order_by: str | None = None,
        limit: int | None = None,
        cursor_field: str | None = None,
        cursor_value: Any | None = None,  # noqa: ANN401
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        """Get records by multiple field filters with optional ordering and pagination.

        Args:
            filters: Dictionary of field:value pairs to filter by
            order_by: Column to order by (e.g. "created_at" for ASC, "-created_at" for DESC)
            limit: Maximum number of records to return
            cursor_field: Field to use for cursor-based pagination
            cursor_value: Value to start pagination from (exclusive)
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of matching records
        """
        try:
            query = self.client.table(self.table_name).select("*")

            # Apply filters
            for field, value in filters.items():
                if value is True or value is False:
                    query = query.eq(field, value)
                elif value is None:
                    query = query.is_(field, "null")
                else:
                    query = query.eq(field, value)

            # Apply soft delete filter
            if self.supports_soft_delete and not include_deleted:
                query = query.is_("deleted_at", "null")

            # Apply cursor-based pagination
            if cursor_field and cursor_value is not None:
                # For descending order, use less than (<)
                # For ascending order, use greater than (>)
                if order_by and order_by.startswith("-"):
                    query = query.lt(cursor_field, cursor_value)
                else:
                    query = query.gt(cursor_field, cursor_value)

            # Apply ordering
            if order_by:
                if order_by.startswith("-"):
                    # Descending order
                    query = query.order(order_by[1:], desc=True)
                else:
                    # Ascending order
                    query = query.order(order_by, desc=False)

            # Apply limit
            if limit:
                query = query.limit(limit)

            response = query.execute()
            return cast("list[dict[str, Any]]", response.data or [])
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(
                f"Error getting {self.table_name} by fields {filters}: {e!s}"
            )

    async def count_by_fields(  # check_unused_code: ignore
        self, filters: dict[str, Any], include_deleted: bool = False
    ) -> int:
        """Count records matching multiple field filters.

        Args:
            filters: Dictionary of field:value pairs to filter by
            include_deleted: Whether to include soft-deleted records

        Returns:
            Count of matching records
        """
        try:
            query = self.client.table(self.table_name).select(
                "id", count=CountMethod.exact
            )

            # Apply filters
            for field, value in filters.items():
                if value is True or value is False:
                    query = query.eq(field, value)
                elif value is None:
                    query = query.is_(field, "null")
                else:
                    query = query.eq(field, value)

            # Apply soft delete filter
            if self.supports_soft_delete and not include_deleted:
                query = query.is_("deleted_at", "null")

            response = query.execute()
            return response.count or 0
        except Exception as e:
            self._check_and_record_connection_error(e)
            raise Exception(
                f"Error counting {self.table_name} by fields {filters}: {e!s}"
            )
