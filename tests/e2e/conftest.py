"""Pytest fixtures for E2E tests."""

import json
import os
import re
import tempfile
from collections.abc import Callable, Generator
from contextlib import AbstractContextManager, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import jwt
import pytest
import sourcemap
from playwright.sync_api import Page

from app.core.config import Settings
from supabase import create_client  # type: ignore[import-untyped]

# Shared test password constant - use this instead of hardcoding passwords
TEST_PASSWORD = "TestPassword123!"


def get_base_url() -> str:
    """Get the base URL for testing."""
    return os.getenv("TEST_BASE_URL", "http://localhost:8000")


def get_supabase_client() -> Any:  # noqa: ANN401
    """Get Supabase client for database queries in e2e tests."""
    settings = Settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY are required for e2e tests"
        )

    return create_client(settings.supabase_url, settings.supabase_service_key)


def seed_user_with_auth(email: str, password: str, full_name: str) -> str:
    """Create user directly in Supabase Auth + users table (bypasses UI).

    Args:
        email: User email
        password: User password
        full_name: User's full name

    Returns:
        User ID (UUID string)
    """
    client = get_supabase_client()

    try:
        # Create user in Supabase Auth using admin API
        auth_response = client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,  # Skip email confirmation for tests
                "user_metadata": {"full_name": full_name},
            }
        )

        if not auth_response.user:
            raise Exception(f"Failed to create auth user for {email}")

        user_id = auth_response.user.id

        # Create user record in users table
        user_data = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }

        client.table("users").insert(user_data).execute()

        return user_id

    except Exception as e:
        # If user already exists, try to get their ID
        if "already been registered" in str(e).lower() or "duplicate" in str(e).lower():
            try:
                response = (
                    client.table("users").select("id").eq("email", email).execute()
                )
                if response.data:
                    return response.data[0]["id"]
            except Exception:
                pass
        raise Exception(f"Failed to seed user {email}: {e}")


def set_auth_session(page: Page, user_id: str) -> None:
    """Set authentication session via Playwright (bypasses UI login).

    Uses JWT token injection to authenticate the browser.

    Args:
        page: Playwright page object
        user_id: User ID to authenticate as
    """
    client = get_supabase_client()
    settings = Settings()

    try:
        # Get user data
        user_response = client.table("users").select("*").eq("id", user_id).execute()
        if not user_response.data:
            raise Exception(f"User not found: {user_id}")

        user = user_response.data[0]

        # Create a JWT token for the user
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)

        payload = {
            "sub": user_id,
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }

        # Sign the token
        token = jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        # Inject the token as a cookie via Playwright
        base_url = get_base_url()
        parsed_url = urlparse(base_url)

        # Navigate to the site first (required to set cookies)
        page.goto(base_url)

        # Set the auth token as an HTTP cookie
        page.context.add_cookies(
            [
                {
                    "name": "access_token",
                    "value": token,
                    "domain": parsed_url.hostname or "localhost",
                    "path": "/",
                    "httpOnly": False,
                    "secure": parsed_url.scheme == "https",
                    "sameSite": "Lax",
                }
            ]
        )

        # Reload the page to ensure the cookie is picked up
        page.reload()

    except Exception as e:
        raise Exception(f"Failed to set auth session for user {user_id}: {e}")


def resolve_stack_trace(stack_trace: str, base_url: str) -> str:
    """Resolve minified stack trace to original source locations using sourcemaps."""
    if not stack_trace:
        return ""

    resolved_lines: list[str] = []
    stack_pattern = re.compile(
        r"at\s+(?:([^\(]+)\s+\()?(.+?):(\d+):(\d+)\)?$", re.MULTILINE
    )

    for line in stack_trace.split("\n"):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        match = stack_pattern.search(stripped_line)
        if not match:
            resolved_lines.append(stripped_line)
            continue

        function_name = match.group(1) or ""
        url = match.group(2)
        line_num = int(match.group(3))
        column_num = int(match.group(4))

        # Convert URL to local file path
        if url.startswith(base_url + "/dist/"):
            dist_path = url.replace(base_url + "/dist/", "")
            js_file = Path("dist") / dist_path
            map_file = Path(str(js_file) + ".map")

            if map_file.exists():
                try:
                    with open(map_file) as f:
                        index = sourcemap.load(f)
                        token = index.lookup(line=line_num - 1, column=column_num)

                        if token and token.src:
                            original_location = (
                                f"{token.src}:{token.src_line + 1}:{token.src_col}"
                            )
                            if token.name:
                                resolved_lines.append(
                                    f"at {token.name} ({original_location})"
                                )
                            elif function_name:
                                resolved_lines.append(
                                    f"at {function_name} ({original_location})"
                                )
                            else:
                                resolved_lines.append(f"at {original_location}")
                            continue
                except Exception:
                    pass

        resolved_lines.append(stripped_line)

    return "\n".join(resolved_lines)


@pytest.fixture(scope="session")
def expected_errors_file() -> Path:
    """Create a session-scoped temp file to store expected HTTP errors for server log analysis."""
    temp_file = Path(tempfile.gettempdir()) / "e2e_expected_errors.txt"
    temp_file.write_text("")
    return temp_file


@pytest.fixture
def error_tracker(expected_errors_file: Path) -> Generator[Any, None, None]:
    """Shared error tracking for all pages in a test."""
    http_errors = []
    console_errors = []
    expected_errors = []

    def expect_http_error(method: str, path: str, status: int) -> None:
        """Mark an HTTP error as expected for this test."""
        expected_errors.append((method, path, status))
        with open(expected_errors_file, "a") as f:
            f.write(
                json.dumps({"method": method, "path": path, "status": status}) + "\n"
            )

    class ErrorTracker:
        def __init__(self) -> None:
            self.http_errors: list = []
            self.console_errors: list = []
            self.expected_errors: list = []
            self.expect_http_error: Any = None

    tracker = ErrorTracker()
    tracker.http_errors = http_errors
    tracker.console_errors = console_errors
    tracker.expected_errors = expected_errors
    tracker.expect_http_error = expect_http_error

    yield tracker

    # Cleanup: Check for errors after test completes
    error_messages = []

    if http_errors:
        error_messages.append("\nHTTP Error Responses:")
        for err in http_errors:
            error_messages.append(
                f"  {err['status']} {err['status_text']} - {err['url']}"
            )

    # Filter out "Failed to fetch" errors - benign during navigation cleanup
    filtered_console_errors = [
        err for err in console_errors if "Failed to fetch" not in err.get("text", "")
    ]

    if filtered_console_errors:
        error_messages.append("\nConsole Errors:")
        for err in filtered_console_errors:
            error_messages.append(f"  {err['text']}")

            if err.get("stack"):
                resolved_stack = resolve_stack_trace(err["stack"], get_base_url())
                if resolved_stack:
                    error_messages.append("    Source-mapped stack trace:")
                    for line in resolved_stack.split("\n"):
                        if line.strip():
                            error_messages.append(f"      {line}")
                else:
                    error_messages.append("    Stack trace:")
                    for line in err["stack"].split("\n"):
                        if line.strip():
                            error_messages.append(f"      {line}")
            elif err["location"]:
                location = err["location"]
                error_messages.append(
                    f"    at {location.get('url', 'unknown')}:{location.get('lineNumber', '?')}"
                )

    if error_messages:
        pytest.fail("\n".join(error_messages))


@pytest.fixture(autouse=True)
def setup_test_environment(
    page: Page, error_tracker: Any  # noqa: ANN401
) -> Generator[None, None, None]:
    """Setup test environment before each test."""
    page.expect_http_error = error_tracker.expect_http_error  # type: ignore[attr-defined]

    def handle_response(response: Any) -> None:  # noqa: ANN401
        """Track HTTP error responses (4xx and 5xx)."""
        if response.status >= 400:
            response_path = urlparse(response.url).path
            response_method = response.request.method

            is_expected = any(
                response.status == expected_status
                and re.match(expected_method, response_method)
                and re.search(expected_path, response_path)
                for expected_method, expected_path, expected_status in error_tracker.expected_errors
            )
            if not is_expected:
                error_tracker.http_errors.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "status_text": response.status_text,
                    }
                )

    def handle_console(msg: Any) -> None:  # noqa: ANN401
        """Track console.error messages with full stack traces."""
        if msg.type == "error":
            is_expected_http_error = False
            if "Failed to load resource" in msg.text and msg.location:
                url = msg.location.get("url", "")
                console_path = urlparse(url).path
                console_method = "GET"

                status_match = re.search(r"\b(\d{3})\s+\(", msg.text)
                if status_match:
                    status_code = int(status_match.group(1))
                    is_expected_http_error = any(
                        status_code == expected_status
                        and re.match(expected_method, console_method)
                        and re.search(expected_path, console_path)
                        for expected_method, expected_path, expected_status in error_tracker.expected_errors
                    )

            if not is_expected_http_error:
                stack_trace = None
                try:
                    args = msg.args
                    if args:
                        for arg in args:
                            try:
                                stack_value = arg.evaluate("arg => arg?.stack")
                                if stack_value and "Error:" in stack_value:
                                    stack_trace = stack_value
                                    break
                            except Exception:
                                continue
                except Exception:
                    pass

                error_tracker.console_errors.append(
                    {
                        "text": msg.text,
                        "location": msg.location,
                        "stack": stack_trace,
                    }
                )

    # Register listeners
    page.on("response", handle_response)
    page.on("console", handle_console)

    yield

    # Cleanup: Remove listeners
    page.remove_listener("response", handle_response)
    page.remove_listener("console", handle_console)


@pytest.fixture
def page_factory(
    page: Page, error_tracker: Any  # noqa: ANN401
) -> Callable[[], AbstractContextManager[Page]]:
    """Factory for creating additional tracked pages in a test."""

    @contextmanager
    def create_page() -> Generator[Page, None, None]:
        browser = page.context.browser
        assert browser is not None, "Browser is required to create additional pages"

        context = browser.new_context()
        new_page = context.new_page()

        def handle_response(response: Any) -> None:  # noqa: ANN401
            if response.status >= 400:
                response_path = urlparse(response.url).path
                response_method = response.request.method

                is_expected = any(
                    response.status == expected_status
                    and re.match(expected_method, response_method)
                    and re.search(expected_path, response_path)
                    for expected_method, expected_path, expected_status in error_tracker.expected_errors
                )
                if not is_expected:
                    error_tracker.http_errors.append(
                        {
                            "url": response.url,
                            "status": response.status,
                            "status_text": response.status_text,
                        }
                    )

        def handle_console(msg: Any) -> None:  # noqa: ANN401
            if msg.type == "error":
                is_expected_http_error = False
                if "Failed to load resource" in msg.text and msg.location:
                    url = msg.location.get("url", "")
                    console_path = urlparse(url).path
                    console_method = "GET"

                    status_match = re.search(r"\b(\d{3})\s+\(", msg.text)
                    if status_match:
                        status_code = int(status_match.group(1))
                        is_expected_http_error = any(
                            status_code == expected_status
                            and re.match(expected_method, console_method)
                            and re.search(expected_path, console_path)
                            for expected_method, expected_path, expected_status in error_tracker.expected_errors
                        )

                if not is_expected_http_error:
                    stack_trace = None
                    try:
                        args = msg.args
                        if args:
                            for arg in args:
                                try:
                                    stack_value = arg.evaluate("arg => arg?.stack")
                                    if stack_value and "Error:" in stack_value:
                                        stack_trace = stack_value
                                        break
                                except Exception:
                                    continue
                    except Exception:
                        pass

                    error_tracker.console_errors.append(
                        {
                            "text": msg.text,
                            "location": msg.location,
                            "stack": stack_trace,
                        }
                    )

        new_page.on("response", handle_response)
        new_page.on("console", handle_console)

        try:
            yield new_page
        finally:
            new_page.remove_listener("response", handle_response)
            new_page.remove_listener("console", handle_console)
            context.close()

    return create_page
