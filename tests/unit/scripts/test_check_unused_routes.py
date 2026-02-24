"""Tests for the unused routes checker script."""

from pathlib import Path
from unittest.mock import mock_open, patch

from scripts.check_unused_routes import extract_api_calls_from_ts_file

MULTI_SCOPE_ENDPOINT_CONTENT = """\
  const handleDelete = async (itemId: string, type: string) => {
    const endpoint =
      type === 'greeting'
        ? `/api/greetings/${itemId}`
        : `/api/users/${itemId}`;

    const response = await fetch(endpoint, { method: 'DELETE' });
  };

  const handleResend = async (notificationId: string, type: string) => {
    const endpoint =
      type === 'email'
        ? `/api/notifications/${notificationId}/resend`
        : type === 'greeting'
          ? `/api/greetings/${notificationId}/notifications/resend`
          : `/api/users/${notificationId}/notifications/resend`;
    const response = await fetch(endpoint, { method: 'POST' });
  };
"""


class TestVariableFetchUsesNearestAssignment:
    """Test that fetch(variable) matches only the nearest preceding variable assignment."""

    def test_delete_fetch_only_gets_delete_paths(self) -> None:
        """The DELETE fetch(endpoint) should only pick up delete paths, not resend paths."""
        with patch("builtins.open", mock_open(read_data=MULTI_SCOPE_ENDPOINT_CONTENT)):
            api_calls = extract_api_calls_from_ts_file(Path("fake.tsx"))

        # Collect all DELETE calls
        delete_calls = {path for method, path in api_calls if method == "DELETE"}
        # The resend paths should NOT appear as DELETE
        for path in delete_calls:
            assert (
                "/resend" not in path
            ), f"DELETE should not be associated with resend path: {path}"

    def test_post_fetch_only_gets_resend_paths(self) -> None:
        """The POST fetch(endpoint) should only pick up resend paths, not delete paths."""
        with patch("builtins.open", mock_open(read_data=MULTI_SCOPE_ENDPOINT_CONTENT)):
            api_calls = extract_api_calls_from_ts_file(Path("fake.tsx"))

        # Collect all POST call paths
        post_paths = {path for method, path in api_calls if method == "POST"}
        # Resend paths should be POST
        assert any(
            "/resend" in p for p in post_paths
        ), f"POST calls should include resend paths, got: {post_paths}"
        # Delete-only paths should NOT be POST
        for path in post_paths:
            assert (
                "/resend" in path or "/notifications/" in path
            ), f"POST should not be associated with delete-only path: {path}"

    def test_no_cross_contamination_between_scopes(self) -> None:
        """Each fetch call should only be associated with paths from its nearest assignment."""
        with patch("builtins.open", mock_open(read_data=MULTI_SCOPE_ENDPOINT_CONTENT)):
            api_calls = extract_api_calls_from_ts_file(Path("fake.tsx"))

        # There should be exactly:
        # - 2 DELETE calls (greetings/{id} and users/{id})
        # - 3 POST calls (the 3 resend paths)
        delete_calls = {(m, p) for m, p in api_calls if m == "DELETE"}
        post_calls = {(m, p) for m, p in api_calls if m == "POST"}

        assert (
            len(delete_calls) == 2
        ), f"Expected 2 DELETE calls, got {len(delete_calls)}: {delete_calls}"
        assert (
            len(post_calls) == 3
        ), f"Expected 3 POST calls, got {len(post_calls)}: {post_calls}"
