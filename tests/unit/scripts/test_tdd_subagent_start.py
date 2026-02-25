"""Tests for tdd_subagent_start: SubagentStart hook creates log and injects context."""

import io
import json
from pathlib import Path

import pytest

from scripts.tdd_subagent_start import main


def test_subagent_start_creates_log_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Calling main() with agent_id should create tdd-agent-{agent_id}.log in cwd."""
    monkeypatch.chdir(tmp_path)

    input_data = {"agent_id": "abc123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))

    main()

    log_file = tmp_path / "tdd-agent-abc123.log"
    assert log_file.exists()


def test_subagent_start_outputs_additional_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """main() should output JSON with hookSpecificOutput.additionalContext containing agent_id and log path."""
    monkeypatch.chdir(tmp_path)

    input_data = {"agent_id": "xyz789"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))

    main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert "hookSpecificOutput" in output
    assert "additionalContext" in output["hookSpecificOutput"]

    context = output["hookSpecificOutput"]["additionalContext"]
    assert "tdd-agent-xyz789.log" in context
    assert "xyz789" in context
    assert "tdd_log" in context  # Should contain usage instructions
