"""Tests for retry decorator."""

import time
from unittest.mock import Mock, patch

import pytest

from app.core.retry import retry_on_error


class TestRetryDecorator:
    """Test the retry_on_error decorator."""

    def test_successful_retry_after_transient_failure(self) -> None:
        """Test that function succeeds after transient failures and records metrics."""
        mock_func = Mock(side_effect=[Exception("Transient error"), "success"])

        with (
            patch("app.core.retry.record_retry_attempt") as mock_retry_metric,
            patch("app.core.retry.record_retry_success") as mock_success_metric,
        ):

            @retry_on_error(
                max_attempts=3,
                initial_delay=0.01,
                retryable_exceptions=[Exception],
                operation="test_operation",
            )
            def test_function() -> str:
                return mock_func()

            result = test_function()
            assert result == "success"
            assert mock_func.call_count == 2  # Failed once, succeeded on retry

            # Verify metrics were recorded
            mock_retry_metric.assert_called_once_with(operation="test_operation")
            mock_success_metric.assert_called_once_with(operation="test_operation")

    def test_max_attempts_exhausted(self) -> None:
        """Test that exception is raised after max attempts exhausted and failure metric recorded."""
        mock_func = Mock(
            side_effect=[
                Exception("Error 1"),
                Exception("Error 2"),
                Exception("Error 3"),
            ]
        )

        with (
            patch("app.core.retry.record_retry_attempt") as mock_retry_metric,
            patch("app.core.retry.record_retry_failed") as mock_failed_metric,
        ):

            @retry_on_error(
                max_attempts=3,
                initial_delay=0.01,
                retryable_exceptions=[Exception],
                operation="test_operation",
            )
            def test_function() -> str:
                return mock_func()

            with pytest.raises(Exception, match="Error 3"):
                test_function()
            assert mock_func.call_count == 3

            # Verify retry attempts were recorded (2 retries after first failure)
            assert mock_retry_metric.call_count == 2
            # Verify final failure was recorded
            mock_failed_metric.assert_called_once_with(operation="test_operation")

    def test_exponential_backoff_timing(self) -> None:
        """Test that exponential backoff delays are applied correctly."""
        call_times: list[float] = []

        def track_time() -> str:
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Retry me")
            return "success"

        @retry_on_error(
            max_attempts=3,
            initial_delay=0.1,
            max_delay=1.0,
            backoff_multiplier=2,
            retryable_exceptions=[Exception],
        )
        def test_function() -> str:
            return track_time()

        result = test_function()
        assert result == "success"
        assert len(call_times) == 3

        # Check delays between attempts
        # First retry: ~0.1s delay
        delay1 = call_times[1] - call_times[0]
        assert 0.08 < delay1 < 0.15  # Allow some tolerance

        # Second retry: ~0.2s delay (0.1 * 2)
        delay2 = call_times[2] - call_times[1]
        assert 0.18 < delay2 < 0.25

    def test_non_retryable_error_raises_immediately(self) -> None:
        """Test that non-retryable errors raise immediately without retry."""
        mock_func = Mock(side_effect=ValueError("Not retryable"))

        @retry_on_error(
            max_attempts=3, initial_delay=0.01, retryable_exceptions=[ConnectionError]
        )
        def test_function() -> str:
            return mock_func()

        with pytest.raises(ValueError, match="Not retryable"):
            test_function()
        assert mock_func.call_count == 1  # No retries

    def test_retryable_error_pattern_matching(self) -> None:
        """Test that errors matching string patterns are retried."""

        @retry_on_error(
            max_attempts=3,
            initial_delay=0.01,
            retryable_patterns=["timeout", "gateway error"],
        )
        def test_function(error_msg: str) -> None:
            raise Exception(error_msg)

        # Should retry "timeout" errors
        call_count = 0

        def timeout_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Connection timeout occurred")
            return "success"

        @retry_on_error(
            max_attempts=3, initial_delay=0.01, retryable_patterns=["timeout"]
        )
        def retry_timeout() -> str:
            return timeout_func()

        result = retry_timeout()
        assert result == "success"
        assert call_count == 2

    def test_preserves_exception_traceback(self) -> None:
        """Test that original exception traceback is preserved."""

        def inner_function() -> None:
            raise ValueError("Original error from inner function")

        @retry_on_error(
            max_attempts=2, initial_delay=0.01, retryable_exceptions=[ValueError]
        )
        def outer_function() -> None:
            inner_function()

        with pytest.raises(
            ValueError, match="Original error from inner function"
        ) as exc_info:
            outer_function()

        # Check that traceback includes the line where the error was raised
        # The traceback should show the full call stack including inner_function
        traceback_entries = list(exc_info.traceback)
        assert (
            len(traceback_entries) >= 3
        )  # Should have outer_function, wrapper, inner_function
