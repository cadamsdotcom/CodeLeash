"""Retry decorator for handling transient failures."""

import asyncio
import functools
import inspect
import logging
import time
from collections.abc import Callable
from typing import Any

from app.core.metrics import (
    record_retry_attempt,
    record_retry_failed,
    record_retry_success,
)

logger = logging.getLogger(__name__)


def retry_on_error(  # check_unused_code: ignore
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_multiplier: float = 2.0,
    retryable_exceptions: list[type[Exception]] | None = None,
    retryable_patterns: list[str] | None = None,
    operation: str = "unknown",
) -> Callable:
    """
    Decorator to retry a function on transient errors.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 30.0)
        backoff_multiplier: Exponential backoff multiplier (default: 2.0)
        retryable_exceptions: List of exception types to retry on
        retryable_patterns: List of string patterns to match in exception messages
        operation: Operation name for metrics (default: "unknown")

    Example:
        @retry_on_error(max_attempts=3, retryable_exceptions=[TimeoutError], operation="my_operation")
        def my_function():
            # This will retry up to 3 times on TimeoutError
            pass
    """

    def decorator(func: Callable) -> Callable:

        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
                delay = initial_delay
                last_exception = None
                did_retry = False

                for attempt in range(1, max_attempts + 1):
                    try:
                        result = await func(*args, **kwargs)
                        # If we retried and succeeded, record success metric
                        if did_retry:
                            record_retry_success(operation=operation)
                        return result
                    except Exception as e:
                        last_exception = e

                        # Check if this exception should be retried
                        should_retry = False

                        # Check if exception type matches retryable exceptions
                        if retryable_exceptions:
                            should_retry = isinstance(e, tuple(retryable_exceptions))

                        # Check if exception message matches retryable patterns
                        if retryable_patterns and not should_retry:
                            error_msg = str(e)
                            should_retry = any(
                                pattern in error_msg for pattern in retryable_patterns
                            )

                        # If not retryable, raise immediately
                        if not should_retry:
                            raise

                        # If this was the last attempt, record failure and raise
                        if attempt >= max_attempts:
                            record_retry_failed(operation=operation)
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e!s}"
                            )
                            raise

                        # Record retry attempt
                        record_retry_attempt(operation=operation)
                        did_retry = True

                        # Log retry attempt
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e!s}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        # Wait before retrying (async sleep)
                        await asyncio.sleep(delay)

                        # Calculate next delay with exponential backoff
                        delay = min(delay * backoff_multiplier, max_delay)

                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
                delay = initial_delay
                last_exception = None
                did_retry = False

                for attempt in range(1, max_attempts + 1):
                    try:
                        result = func(*args, **kwargs)
                        # If we retried and succeeded, record success metric
                        if did_retry:
                            record_retry_success(operation=operation)
                        return result
                    except Exception as e:
                        last_exception = e

                        # Check if this exception should be retried
                        should_retry = False

                        # Check if exception type matches retryable exceptions
                        if retryable_exceptions:
                            should_retry = isinstance(e, tuple(retryable_exceptions))

                        # Check if exception message matches retryable patterns
                        if retryable_patterns and not should_retry:
                            error_msg = str(e)
                            should_retry = any(
                                pattern in error_msg for pattern in retryable_patterns
                            )

                        # If not retryable, raise immediately
                        if not should_retry:
                            raise

                        # If this was the last attempt, record failure and raise
                        if attempt >= max_attempts:
                            record_retry_failed(operation=operation)
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e!s}"
                            )
                            raise

                        # Record retry attempt
                        record_retry_attempt(operation=operation)
                        did_retry = True

                        # Log retry attempt
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e!s}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        # Wait before retrying
                        time.sleep(delay)

                        # Calculate next delay with exponential backoff
                        delay = min(delay * backoff_multiplier, max_delay)

                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception

            return sync_wrapper

    return decorator
