"""Tests for tdd_session_start SessionStart hook."""

import io
import json
from pathlib import Path
from unittest.mock import patch

from scripts.tdd_session_start import main

INPUT_DATA = {
    "transcript_path": "/tmp/transcript-abc123.json",
}


class TestTddSessionStart:
    """Verify the SessionStart hook outputs the TDD log file name."""

    def _run_hook(self, input_data: dict) -> str:
        """Run main() with mocked stdin and capture stdout."""
        stdin_text = json.dumps(input_data)
        stdout = io.StringIO()
        fake_log = Path("tdd-aabb1122.log")

        with (
            patch("sys.stdin", io.StringIO(stdin_text)),
            patch("sys.stdout", stdout),
            patch(
                "scripts.tdd_session_start.get_log_path",
                return_value=fake_log,
            ),
        ):
            main()

        return stdout.getvalue()

    def test_outputs_log_file_name(self) -> None:
        output = self._run_hook(INPUT_DATA)
        assert "tdd-aabb1122.log" in output

    def test_outputs_usage_hint(self) -> None:
        output = self._run_hook(INPUT_DATA)
        assert '--log "tdd-aabb1122.log"' in output

    def test_outputs_red_example(self) -> None:
        output = self._run_hook(INPUT_DATA)
        assert 'scripts.tdd_log --log "tdd-aabb1122.log" red' in output
        assert "--test" in output
        assert "--expects" in output

    def test_outputs_green_example(self) -> None:
        output = self._run_hook(INPUT_DATA)
        assert 'scripts.tdd_log --log "tdd-aabb1122.log" green' in output
        assert "--change" in output
        assert "--file" in output

    def test_outputs_skip_red_example(self) -> None:
        output = self._run_hook(INPUT_DATA)
        assert "--skip-red" in output
        assert "--reason=" in output

    def test_outputs_prod_file_patterns(self) -> None:
        """Output lists which file patterns are subject to TDD as prod files."""
        output = self._run_hook(INPUT_DATA)
        assert "src/" in output
        assert "app/" in output
        assert "scripts/" in output
        assert "main.py" in output
        assert "worker.py" in output

    def test_outputs_test_file_patterns(self) -> None:
        """Output lists which file patterns are subject to TDD as test files."""
        output = self._run_hook(INPUT_DATA)
        assert ".test.{ts,tsx,js,jsx}" in output
        assert "test_*.py" in output

    def test_outputs_bypass_info(self) -> None:
        """Output mentions which files bypass TDD."""
        output = self._run_hook(INPUT_DATA)
        assert "e2e" in output.lower()
        assert "bypass" in output.lower() or "not subject" in output.lower()

    def test_no_transcript_path_uses_default(self) -> None:
        """When no transcript_path provided, still outputs a log name."""
        stdin_text = json.dumps({})
        stdout = io.StringIO()

        with (
            patch("sys.stdin", io.StringIO(stdin_text)),
            patch("sys.stdout", stdout),
        ):
            main()

        output = stdout.getvalue()
        assert "tdd.log" in output
