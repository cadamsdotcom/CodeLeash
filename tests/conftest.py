"""Pytest configuration and shared fixtures for all tests."""

import cProfile
import os
import subprocess
import tempfile
import time
from collections.abc import Generator
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.models.greeting import Greeting
from app.models.user import User


def pytest_report_teststatus(
    report: Any, config: Any  # noqa: ANN401
) -> tuple[str, str, str] | None:
    """Suppress pytest dots/progress output for passing tests."""
    _ = config  # required by pytest hook signature
    if report.passed and report.when == "call":
        return report.outcome, "", report.outcome.upper()


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Mock Supabase client for database operations."""
    client = MagicMock()

    # Default successful response
    client.table.return_value.select.return_value.execute.return_value.data = []
    client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "test-id"}
    ]
    client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {"id": "test-id"}
    ]
    client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = (
        []
    )

    return client


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    return User(
        id="user-123",
        email="user@example.com",
        full_name="Test User",
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_greeting() -> Greeting:
    """Create a mock greeting."""
    return Greeting(
        id="greeting-001",
        message="Hello from CodeLeash!",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deleted_at=None,
    )


@pytest.fixture
def mock_repository_base() -> MagicMock:
    """Mock base repository with common methods."""
    repo = MagicMock()

    repo.get.return_value = {"id": "test-id"}
    repo.create.return_value = {"id": "test-id"}
    repo.update.return_value = {"id": "test-id"}
    repo.delete.return_value = True
    repo.list.return_value = []

    return repo


class TestTimeoutError(Exception):
    """Exception raised when test logic exceeds 10ms limit."""

    pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: Any) -> Generator[None, None, None]:  # noqa: ANN401
    """Enforce 10ms timeout on unit test logic with one automatic retry for transient performance issues."""
    # Only apply to tests in tests/unit/ directory
    if "tests/unit/" not in item.fspath.strpath:
        # Let pytest handle non-unit tests normally
        yield
        return

    # Check if this is a retry attempt
    retrying = getattr(item, "_timeout_retry", False)

    # Run the test and measure performance
    profiler = cProfile.Profile()

    # Enable profiling
    profiler.enable()

    # Time the actual test execution (excluding profiler overhead)
    start_time = time.perf_counter_ns()
    try:
        yield
    finally:
        end_time = time.perf_counter_ns()
        duration_ms = (end_time - start_time) / 1_000_000
        profiler.disable()

    # Check if test exceeded 10ms limit
    if duration_ms > 10.0:
        # Retry once in case the test was unlucky and triggered heavy init.
        should_retry = not retrying
        if should_retry:

            def retry(the_item: Any) -> None:  # noqa: ANN401
                # Mark as a retry for the recursive call
                the_item._timeout_retry = True
                # Re-run the test by calling the hook recursively
                pytest_runtest_call(the_item)

            # First timeout - retry once
            retry(item)
            return

        # Second timeout - generate flamegraph and fail
        test_name = item.nodeid

        # Generate flamegraph for slow test
        flamegraph_path = _generate_flamegraph(profiler, item, duration_ms)

        error_msg = f"""Test logic exceeded 10ms limit after retry: {duration_ms:.3f}ms

This test must only exercise your project's own business logic code.
If failing:
- Mock all external dependencies (database, APIs, file I/O)
- Extract complex setup into fixtures (not timed)
- Focus test on pure computational logic only
- Consider if this should be an integration test instead

Test: {test_name}
Flamegraph saved to: {flamegraph_path}
Open the SVG file in a browser to analyze the performance bottleneck."""
        raise TestTimeoutError(error_msg)


def _generate_flamegraph(
    profiler: cProfile.Profile, item: Any, duration_ms: float  # noqa: ANN401
) -> str:
    """Generate a flamegraph from cProfile stats for a slow test."""
    try:
        # Ensure test_profiles directory exists
        os.makedirs("test_profiles", exist_ok=True)

        # Create safe filename from test path
        test_path = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
        # Remove file extension and clean up
        test_path = test_path.replace(".py", "").replace(".", "_")

        # Generate flamegraph filename
        flamegraph_filename = f"{test_path}_{duration_ms:.1f}ms.svg"
        flamegraph_path = os.path.join("test_profiles", flamegraph_filename)

        # Create temporary file for cProfile stats
        with tempfile.NamedTemporaryFile(suffix=".prof", delete=False) as temp_prof:
            profiler.dump_stats(temp_prof.name)

            # Use flameprof command-line to generate flamegraph
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "flameprof",
                    "--out",
                    flamegraph_path,
                    temp_prof.name,
                ],
                capture_output=True,
                text=True,
            )

            # Clean up temporary file
            os.unlink(temp_prof.name)

            if result.returncode == 0:
                return flamegraph_path
            else:
                return (
                    f"Failed to generate flamegraph: {result.stderr or result.stdout}"
                )

    except ImportError:
        # Fallback if flameprof is not available
        return "flameprof not available - install with: uv add --dev flameprof"
    except Exception as e:
        # Fallback if flamegraph generation fails
        return f"Failed to generate flamegraph: {e}"
