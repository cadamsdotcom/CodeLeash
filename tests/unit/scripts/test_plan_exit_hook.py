"""Unit tests for plan_exit_hook.py - ExitPlanMode TDD review hook."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.plan_exit_hook import get_nested_claude_review, get_state_file, main


class TestGetStateFile:
    """Tests for get_state_file function."""

    def test_state_file_uses_session_id(self) -> None:
        """State file path includes session ID."""
        state_file = get_state_file("test-session-123")

        assert state_file.parent == Path("/tmp")
        assert state_file.name == ".claude-plan-reviewed-test-session-123"

    def test_different_sessions_different_state_files(self) -> None:
        """Different session IDs produce different state file paths."""
        state_file_1 = get_state_file("session-a")
        state_file_2 = get_state_file("session-b")

        assert state_file_1 != state_file_2

    def test_same_session_same_state_file(self) -> None:
        """Same session ID produces same state file path."""
        state_file_1 = get_state_file("session-abc")
        state_file_2 = get_state_file("session-abc")

        assert state_file_1 == state_file_2


class TestMainFlow:
    """Tests for the main hook flow."""

    @staticmethod
    def make_stdin_json(session_id: str, plan_content: str = "") -> str:
        """Create stdin JSON with session_id and optional plan content."""
        return json.dumps(
            {
                "session_id": session_id,
                "tool_input": {"plan": plan_content} if plan_content else {},
            }
        )

    def test_blocks_first_call_allows_second(self) -> None:
        """First call blocks (exit 2), second call allows (exit 0)."""
        session_id = "test-blocks-first"
        plan_content = "# Test Plan\n\nSome implementation details."
        stdin_json = self.make_stdin_json(session_id, plan_content)

        # Clean up any existing state file
        state_file = Path(f"/tmp/.claude-plan-reviewed-{session_id}")
        if state_file.exists():
            state_file.unlink()

        with (
            patch("sys.stdin.read", return_value=stdin_json),
            patch(
                "scripts.plan_exit_hook.get_nested_claude_review",
                return_value="Mock review",
            ),
        ):
            # First call should block (exit 2)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

            # Second call should allow (exit 0)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_different_sessions_each_get_one_review(self) -> None:
        """Different session IDs each trigger their own review cycle."""
        plan_content = "# Test Plan"

        # Clean up state files for these sessions
        for session in ["session-a", "session-b"]:
            state_file = Path(f"/tmp/.claude-plan-reviewed-{session}")
            if state_file.exists():
                state_file.unlink()

        with patch(
            "scripts.plan_exit_hook.get_nested_claude_review",
            return_value="Mock review",
        ):
            # Session A first call blocks
            with patch(
                "sys.stdin.read",
                return_value=self.make_stdin_json("session-a", plan_content),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2

            # Session A second call allows
            with patch(
                "sys.stdin.read",
                return_value=self.make_stdin_json("session-a", plan_content),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

            # Session B first call blocks (different session)
            with patch(
                "sys.stdin.read",
                return_value=self.make_stdin_json("session-b", plan_content),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2

    def test_passes_plan_content_to_review(self) -> None:
        """Plan content from stdin is passed to nested Claude review."""
        session_id = "test-plan-content"
        plan_content = "# My Plan\n\nImplementation details here."
        stdin_json = self.make_stdin_json(session_id, plan_content)

        state_file = Path(f"/tmp/.claude-plan-reviewed-{session_id}")
        if state_file.exists():
            state_file.unlink()

        captured_plan = []

        def capture_plan(content: str) -> str:
            captured_plan.append(content)
            return "Mock review"

        with (
            patch("sys.stdin.read", return_value=stdin_json),
            patch(
                "scripts.plan_exit_hook.get_nested_claude_review",
                side_effect=capture_plan,
            ),
            pytest.raises(SystemExit),
        ):
            main()

        assert len(captured_plan) == 1
        assert captured_plan[0] == plan_content

    def test_handles_empty_plan_content(self) -> None:
        """Handles case where plan content is empty."""
        session_id = "test-empty-plan"
        stdin_json = self.make_stdin_json(session_id, "")

        state_file = Path(f"/tmp/.claude-plan-reviewed-{session_id}")
        if state_file.exists():
            state_file.unlink()

        captured_plan = []

        def capture_plan(content: str) -> str:
            captured_plan.append(content)
            return "Mock review"

        with (
            patch("sys.stdin.read", return_value=stdin_json),
            patch(
                "scripts.plan_exit_hook.get_nested_claude_review",
                side_effect=capture_plan,
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should still block on first call
            assert exc_info.value.code == 2

        # Should pass empty string to nested review
        assert len(captured_plan) == 1
        assert captured_plan[0] == ""


class TestNestedClaudeReview:
    """Tests for get_nested_claude_review function."""

    def test_returns_stdout_on_success(self) -> None:
        """Returns Claude's stdout when successful."""
        mock_result = MagicMock(stdout="  Review feedback here  ", returncode=0)

        with patch("subprocess.run", return_value=mock_result):
            result = get_nested_claude_review("Test plan")
            assert result == "Review feedback here"

    def test_returns_message_on_timeout(self) -> None:
        """Returns timeout message when Claude times out."""
        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 60)
        ):
            result = get_nested_claude_review("Test plan")
            assert "timed out" in result.lower()

    def test_returns_message_when_cli_not_found(self) -> None:
        """Returns not found message when Claude CLI is missing."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = get_nested_claude_review("Test plan")
            assert "not found" in result.lower()
