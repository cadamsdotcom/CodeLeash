"""Tests for tdd_pre_edit: edit blocking, classification, and state transitions."""

import io
import json
from pathlib import Path

import pytest

from scripts.tdd_pre_edit import (
    classify_file,
    main,
    read_green_allowlist,
    read_state,
    warn_large_allowlist,
)


def _write_log(log_path: Path, content: str) -> None:
    """Write content to a TDD log file."""
    log_path.write_text(content)


def test_edit_test_during_green_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test edits are blocked during non-skip-red making_tests_pass.

    This prevents modifying tests (changing the definition of 'red')
    and then editing prod code without re-verifying the test fails.
    """
    log_path = tmp_path / "tdd-test.log"

    # Set up making_tests_pass state (non-skip-red)
    _write_log(
        log_path,
        "## Green — 2026-01-01T00:00:00+00:00\n"
        "Change: implement feature\n"
        "File: src/foo.py\n\n",
    )

    input_data = {
        "tool_input": {
            "file_path": "src/components/Foo.test.tsx",
            "old_string": "expect(x).toBe(1)",
            "new_string": "expect(x).toBe(2)",
        },
        "transcript_path": "",
    }

    monkeypatch.setattr("scripts.tdd_pre_edit.get_log_path", lambda _: log_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


def test_edit_test_during_skip_red_green_is_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test edits are allowed during skip-red making_tests_pass.

    skip-red with adding-coverage means tests are expected to pass immediately,
    so blocking test edits would prevent the intended workflow.
    """
    log_path = tmp_path / "tdd-test.log"

    # Set up skip-red making_tests_pass state
    _write_log(
        log_path,
        "## Green (skip-red) — 2026-01-01T00:00:00+00:00\n"
        "Change: add test coverage\n"
        "File: tests/test_foo.py\n"
        "Reason: adding-coverage\n\n",
    )

    input_data = {
        "tool_input": {
            "file_path": "tests/test_foo.py",
            "old_string": "old",
            "new_string": "new",
        },
        "transcript_path": "",
    }

    monkeypatch.setattr("scripts.tdd_pre_edit.get_log_path", lambda _: log_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_classify_test_utils_as_test() -> None:
    """Files in src/test-utils/ should be classified as test files."""
    assert classify_file("src/test-utils/helpers.ts") == "test"


def test_large_green_allowlist_emits_warning(tmp_path: Path, capsys: object) -> None:
    """A Green allowlist with >5 files should emit a stderr warning."""
    log_path = tmp_path / "tdd-test.log"

    # Create a making_tests_pass state with 7 files
    files = [f"src/file{i}.py" for i in range(7)]
    file_lines = "\n".join(f"File: {f}" for f in files)
    _write_log(
        log_path,
        f"## Green — 2026-01-01T00:00:00+00:00\n"
        f"Change: big change\n"
        f"{file_lines}\n\n",
    )

    warn_large_allowlist(read_green_allowlist(log_path))

    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert "7 files" in captured.err
    assert "Large Green allowlist" in captured.err


def test_small_green_allowlist_no_warning(tmp_path: Path, capsys: object) -> None:
    """A Green allowlist with <=5 files should NOT emit a warning."""
    log_path = tmp_path / "tdd-test.log"

    # Create a making_tests_pass state with 3 files
    _write_log(
        log_path,
        "## Green — 2026-01-01T00:00:00+00:00\n"
        "Change: small change\n"
        "File: src/a.py\n"
        "File: src/b.py\n"
        "File: src/c.py\n\n",
    )

    warn_large_allowlist(read_green_allowlist(log_path))

    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert captured.err == ""


def test_failure_after_making_tests_pass_stays_making_tests_pass(
    tmp_path: Path,
) -> None:
    """A test failure during the Green phase should keep state as making_tests_pass."""
    log_path = tmp_path / "tdd-test.log"

    _write_log(
        log_path,
        "## Green — 2026-01-01T00:00:00+00:00\n"
        "Change: implement feature\n"
        "File: src/foo.py\n\n"
        "[test] npm run test:python — FAILED(1)\n",
    )

    assert read_state(log_path) == "making_tests_pass"


def test_failure_after_writing_tests_becomes_red(tmp_path: Path) -> None:
    """A test failure during the writing-tests phase should transition to red."""
    log_path = tmp_path / "tdd-test.log"

    _write_log(
        log_path,
        "## Red — 2026-01-01T00:00:00+00:00\n"
        "Test: tests/test_foo.py\n"
        "Expects: should fail\n\n"
        "[test] npm run test:python — FAILED(1)\n",
    )

    assert read_state(log_path) == "red"


def test_success_after_making_tests_pass_resets_to_initial(tmp_path: Path) -> None:
    """A test success after making-tests-pass should reset to initial."""
    log_path = tmp_path / "tdd-test.log"

    _write_log(
        log_path,
        "## Green — 2026-01-01T00:00:00+00:00\n"
        "Change: implement feature\n"
        "File: src/foo.py\n\n"
        "[test] npm run test:python — SUCCEEDED\n",
    )

    assert read_state(log_path) == "initial"


# ---------------------------------------------------------------------------
# Fallback chain: per-agent TDD log tests
# ---------------------------------------------------------------------------


def _setup_main_with_agent_logs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parent_log_content: str,
    file_path: str,
) -> None:
    """Set up main() to run with a parent log and agent logs in tmp_path."""
    log_path = tmp_path / "tdd-test.log"
    _write_log(log_path, parent_log_content)

    input_data = {
        "tool_input": {
            "file_path": file_path,
            "old_string": "old",
            "new_string": "new",
        },
        "transcript_path": "",
    }

    monkeypatch.setattr("scripts.tdd_pre_edit.get_log_path", lambda _: log_path)
    monkeypatch.setattr("scripts.tdd_pre_edit.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))


def test_blocked_edit_allowed_by_agent_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A blocked edit (parent in initial) should be allowed if an agent log has the file in its green allowlist."""
    # Create an agent log in making_tests_pass state with the file declared
    agent_log = tmp_path / "tdd-agent-test123.log"
    _write_log(
        agent_log,
        "## Green — 2026-01-01T00:00:00+00:00\n"
        "Change: implement feature\n"
        "File: src/foo.py\n\n",
    )

    _setup_main_with_agent_logs(
        tmp_path,
        monkeypatch,
        parent_log_content="",
        file_path=str(tmp_path / "src" / "foo.py"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_finished_agent_log_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finished agent log (with ## FINISHED marker) should not allow edits."""
    # Create a finished agent log
    agent_log = tmp_path / "tdd-agent-done456.log"
    _write_log(
        agent_log,
        "## Green — 2026-01-01T00:00:00+00:00\n"
        "Change: implement feature\n"
        "File: src/foo.py\n\n"
        "## FINISHED — 2026-01-01T01:00:00+00:00\n",
    )

    _setup_main_with_agent_logs(
        tmp_path,
        monkeypatch,
        parent_log_content="",
        file_path=str(tmp_path / "src" / "foo.py"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


def test_blocked_edit_stays_blocked_without_agent_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A blocked edit with no agent logs should stay blocked."""
    _setup_main_with_agent_logs(
        tmp_path,
        monkeypatch,
        parent_log_content="",
        file_path=str(tmp_path / "src" / "bar.py"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


def test_agent_log_writing_tests_allows_test_edits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An agent log in writing_tests state should allow test file edits."""
    # Create an agent log in writing_tests state
    agent_log = tmp_path / "tdd-agent-red789.log"
    _write_log(
        agent_log,
        "## Red — 2026-01-01T00:00:00+00:00\n"
        "Test: tests/test_foo.py\n"
        "Expects: should fail\n\n",
    )

    _setup_main_with_agent_logs(
        tmp_path,
        monkeypatch,
        parent_log_content="",
        file_path=str(tmp_path / "tests" / "test_foo.py"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
