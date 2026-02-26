"""Tests for tdd_log.py - state validation in cmd_green."""

import argparse
from pathlib import Path

from scripts.tdd_log import cmd_green, cmd_red


def _write_log(log_path: Path, content: str) -> None:
    """Write content to a TDD log file."""
    log_path.write_text(content)


def _make_green_args(
    log: str,
    change: str,
    files: list[str],
    skip_red: bool = False,
    reason: str | None = None,
) -> argparse.Namespace:
    """Build a Namespace that looks like parsed green args."""
    return argparse.Namespace(
        log=log,
        phase="green",
        change=change,
        file=files,
        skip_red=skip_red,
        reason=reason,
    )


def _make_red_args(
    log: str,
    test: str,
    expects: str,
) -> argparse.Namespace:
    """Build a Namespace that looks like parsed red args."""
    return argparse.Namespace(
        log=log,
        phase="red",
        test=test,
        expects=expects,
    )


class TestCmdGreenRequiresRedCycle:
    """cmd_green must reject Green intents when no Red cycle has occurred."""

    def test_rejects_from_initial_state(self, tmp_path: Path) -> None:
        """Green from initial state is rejected - no Red cycle preceded it."""
        log_path = tmp_path / "tdd-test.log"
        # Empty log → initial state
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="implement feature",
            files=["src/foo.py"],
        )

        exit_code = cmd_green(args)

        assert exit_code == 1
        # Log should not have been written to
        assert "## Green" not in log_path.read_text()

    def test_rejects_from_writing_tests_state(self, tmp_path: Path) -> None:
        """Green from writing_tests is rejected - test hasn't been run yet."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="implement feature",
            files=["src/foo.py"],
        )

        exit_code = cmd_green(args)

        assert exit_code == 1
        # Should not append a Green section
        assert log_path.read_text().count("## Green") == 0

    def test_allows_from_red_state(self, tmp_path: Path) -> None:
        """Green from red state is allowed - test was run and failed."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="implement feature",
            files=["src/foo.py"],
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        assert "## Green" in log_path.read_text()

    def test_allows_from_making_tests_pass_state(self, tmp_path: Path) -> None:
        """Green from making_tests_pass is allowed - re-declaring the allowlist."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n"
            "\n## Green - 2026-01-01T00:01:00+00:00\n"
            "Change: implement feature\n"
            "File: src/foo.py\n\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="add another file",
            files=["src/foo.py", "src/bar.py"],
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        # Should have two Green sections now
        assert log_path.read_text().count("## Green") == 2


class TestSkipRedFlag:
    """--skip-red bypasses Red cycle requirement for refactoring changes."""

    def test_skip_red_allows_from_initial_state(self, tmp_path: Path) -> None:
        """--skip-red allows Green from initial state."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Fix lint issues",
            files=["src/foo.py"],
            skip_red=True,
            reason="lint-only",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        assert "## Green" in log_path.read_text()

    def test_skip_red_allows_from_writing_tests_state(self, tmp_path: Path) -> None:
        """--skip-red allows Green even from writing_tests (overrides normal check)."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="Rename variable",
            files=["src/foo.py"],
            skip_red=True,
            reason="refactoring",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        assert "## Green" in log_path.read_text()

    def test_skip_red_logs_distinct_label(self, tmp_path: Path) -> None:
        """--skip-red logs '## Green (skip-red)' to distinguish from normal Green."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Fix lint issues",
            files=["src/foo.py"],
            skip_red=True,
            reason="lint-only",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "## Green (skip-red)" in content


class TestSkipRedRequiresReason:
    """--skip-red requires a valid --reason to constrain abuse."""

    def test_skip_red_without_reason_rejected(self, tmp_path: Path) -> None:
        """--skip-red without --reason is rejected."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Fix lint issues",
            files=["src/foo.py"],
            skip_red=True,
            reason=None,
        )

        exit_code = cmd_green(args)

        assert exit_code == 1
        assert "## Green" not in log_path.read_text()

    def test_skip_red_with_invalid_reason_rejected(self, tmp_path: Path) -> None:
        """--skip-red with invalid --reason is rejected."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Add new feature",
            files=["src/foo.py"],
            skip_red=True,
            reason="i-dont-want-to-test",
        )

        exit_code = cmd_green(args)

        assert exit_code == 1
        assert "## Green" not in log_path.read_text()

    def test_skip_red_with_refactoring_reason_allowed(self, tmp_path: Path) -> None:
        """--skip-red with --reason=refactoring is allowed."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Rename variable foo to bar",
            files=["src/foo.py"],
            skip_red=True,
            reason="refactoring",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "## Green (skip-red)" in content
        assert "Reason: refactoring" in content

    def test_skip_red_with_lint_only_reason_allowed(self, tmp_path: Path) -> None:
        """--skip-red with --reason=lint-only is allowed."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Fix formatting",
            files=["src/foo.py"],
            skip_red=True,
            reason="lint-only",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "## Green (skip-red)" in content
        assert "Reason: lint-only" in content

    def test_skip_red_with_adding_coverage_reason_allowed(self, tmp_path: Path) -> None:
        """--skip-red with --reason=adding-coverage is allowed."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Add test coverage for existing function",
            files=["tests/test_foo.py"],
            skip_red=True,
            reason="adding-coverage",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "## Green (skip-red)" in content
        assert "Reason: adding-coverage" in content


class TestCmdGreenWritesLog:
    """cmd_green writes correct log entries on success."""

    def test_writes_all_files(self, tmp_path: Path) -> None:
        """Green log entry includes all declared files."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="implement feature",
            files=["src/foo.py", "src/bar.py", "src/baz.py"],
        )

        cmd_green(args)

        content = log_path.read_text()
        assert "File: src/foo.py" in content
        assert "File: src/bar.py" in content
        assert "File: src/baz.py" in content
        assert "Change: implement feature" in content


class TestOverrideDetection:
    """cmd_red and cmd_green detect and log state overrides."""

    def test_red_from_writing_tests_is_override(self, tmp_path: Path) -> None:
        """Red from writing_tests state is an override."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n",
        )

        args = _make_red_args(
            log=str(log_path),
            test="tests/test_bar.py",
            expects="different test should fail",
        )

        cmd_red(args)

        content = log_path.read_text()
        assert "(override from writing_tests)" in content

    def test_red_from_making_tests_pass_is_override(self, tmp_path: Path) -> None:
        """Red from making_tests_pass state is an override."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n"
            "\n## Green - 2026-01-01T00:01:00+00:00\n"
            "Change: implement feature\n"
            "File: src/foo.py\n\n",
        )

        args = _make_red_args(
            log=str(log_path),
            test="tests/test_bar.py",
            expects="different test should fail",
        )

        cmd_red(args)

        content = log_path.read_text()
        assert "(override from making_tests_pass)" in content

    def test_red_from_initial_no_override(self, tmp_path: Path) -> None:
        """Red from initial state is not an override (normal start)."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_red_args(
            log=str(log_path),
            test="tests/test_foo.py",
            expects="should fail",
        )

        cmd_red(args)

        content = log_path.read_text()
        assert "(override" not in content
        assert "## Red -" in content

    def test_red_from_red_is_override(self, tmp_path: Path) -> None:
        """Red from red state is an override."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n",
        )

        args = _make_red_args(
            log=str(log_path),
            test="tests/test_bar.py",
            expects="different test should fail",
        )

        cmd_red(args)

        content = log_path.read_text()
        assert "(override from red)" in content

    def test_green_from_making_tests_pass_is_override(self, tmp_path: Path) -> None:
        """Green from making_tests_pass state is an override (re-declaring allowlist)."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n"
            "\n## Green - 2026-01-01T00:01:00+00:00\n"
            "Change: implement feature\n"
            "File: src/foo.py\n\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="add another file",
            files=["src/foo.py", "src/bar.py"],
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "(override from making_tests_pass)" in content

    def test_green_from_red_no_override(self, tmp_path: Path) -> None:
        """Green from red state is not an override (normal flow)."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n"
            "[test] npm run test:python -- tests/test_foo.py - FAILED\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="implement feature",
            files=["src/foo.py"],
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "(override" not in content
        assert "## Green -" in content

    def test_skip_red_from_writing_tests_is_override(self, tmp_path: Path) -> None:
        """Skip-red from writing_tests state is an override."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(
            log_path,
            "## Red - 2026-01-01T00:00:00+00:00\n"
            "Test: tests/test_foo.py\n"
            "Expects: should fail\n\n",
        )

        args = _make_green_args(
            log=str(log_path),
            change="Fix lint issues",
            files=["src/foo.py"],
            skip_red=True,
            reason="lint-only",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "(skip-red, override from writing_tests)" in content

    def test_skip_red_from_initial_no_override(self, tmp_path: Path) -> None:
        """Skip-red from initial state is not an override (normal skip-red use)."""
        log_path = tmp_path / "tdd-test.log"
        _write_log(log_path, "")

        args = _make_green_args(
            log=str(log_path),
            change="Fix lint issues",
            files=["src/foo.py"],
            skip_red=True,
            reason="lint-only",
        )

        exit_code = cmd_green(args)

        assert exit_code == 0
        content = log_path.read_text()
        assert "(override" not in content
        assert "## Green (skip-red) -" in content
