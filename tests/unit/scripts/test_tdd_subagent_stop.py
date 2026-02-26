"""Tests for tdd_subagent_stop: SubagentStop hook writes FINISHED marker."""

import io
import json
from pathlib import Path

import pytest

from scripts.tdd_subagent_stop import main


def test_subagent_stop_writes_finished_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Calling main() should append '## FINISHED' marker to the agent's log file."""
    monkeypatch.chdir(tmp_path)

    # Create an existing agent log file with some content
    log_file = tmp_path / "tdd-agent-abc123.log"
    log_file.write_text("## Red - 2026-01-01T00:00:00+00:00\nTest: tests/test_foo.py\n")

    input_data = {"agent_id": "abc123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))

    main()

    content = log_file.read_text()
    assert "## FINISHED" in content
    # Original content should still be there
    assert "## Red" in content


def test_subagent_stop_noop_if_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Calling main() with an agent_id that has no log file should not error."""
    monkeypatch.chdir(tmp_path)

    input_data = {"agent_id": "nonexistent"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))

    # Should not raise
    main()

    # File should not be created
    assert not (tmp_path / "tdd-agent-nonexistent.log").exists()
