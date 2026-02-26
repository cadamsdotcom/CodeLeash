"""TDD Guard - PreToolUse hook for Edit|Write.

Enforces the Red-Green-Refactor cycle by allowing or blocking file edits
based on the current TDD state derived from the per-agent log.
"""

import glob
import json
import re
import subprocess
import sys
from pathlib import Path

from .tdd_common import get_log_path, is_prod_file, read_state

_project_root: str | None = None


def get_project_root() -> Path:
    """Get the git repo root (cached)."""
    global _project_root
    if _project_root is None:
        try:
            _project_root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            _project_root = str(Path(__file__).resolve().parent.parent)
    return Path(_project_root)


def _to_project_relative(file_path: str) -> str:
    """Convert absolute path to project-relative."""
    root = get_project_root()
    try:
        return str(Path(file_path).relative_to(root))
    except ValueError:
        return file_path


# ---------------------------------------------------------------------------
# File classification patterns (matched against project-relative paths)
# ---------------------------------------------------------------------------

E2E_PATTERNS = [
    r"^tests/e2e/",
]

TEST_PATTERNS = [
    r"\.test\.(ts|tsx|js|jsx)$",
    r"test_.*\.py$",
    r"^tests/",
    r"^src/test-utils/",
    r"conftest\.py$",
]


def classify_file(file_path: str) -> str:
    """Classify a file as 'e2e_test', 'test', 'prod', or 'other'.

    E2E tests and 'other' files bypass the TDD state machine.
    """
    rel_path = _to_project_relative(file_path)
    if any(re.search(p, rel_path) for p in E2E_PATTERNS):
        return "e2e_test"
    if any(re.search(p, rel_path) for p in TEST_PATTERNS):
        return "test"
    if is_prod_file(rel_path):
        return "prod"
    return "other"


def is_skip_red_green(log_path: Path) -> bool:
    """Check if the last ## Green header was a skip-red green."""
    if not log_path.exists():
        return False

    for line in reversed(log_path.read_text().strip().splitlines()):
        stripped = line.rstrip()
        if stripped.startswith("## Green") and "skip-red" in stripped:
            return True
        if stripped.startswith("## Green"):
            return False
    return False


def read_green_allowlist(log_path: Path) -> set[str]:
    """Scan log bottom-up from last ## Green header, collecting File: lines."""
    if not log_path.exists():
        return set()

    lines = log_path.read_text().strip().splitlines()
    allowed: set[str] = set()

    for line in reversed(lines):
        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped.startswith("## Green"):
            break
        if stripped.startswith("File:"):
            allowed.add(stripped[len("File:") :].strip())

    return allowed


def warn_large_allowlist(allowed: set[str], threshold: int = 5) -> None:
    """Emit a stderr warning if the Green allowlist exceeds *threshold* files."""
    if len(allowed) > threshold:
        print(
            f"\u26a0\ufe0f  Large Green allowlist ({len(allowed)} files). "
            "Consider smaller increments.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Blocked messages
# ---------------------------------------------------------------------------


def blocked_initial(log_name: str) -> str:
    return f"""\
BLOCKED: Red-Green-Refactor - log your Red declaration first.
Run (fill in the placeholders):

  uv run python -m scripts.tdd_log --log "{log_name}" red --test "path/to/test_file" --expects "test_name fails because ..." """


def blocked_writing_tests_impl() -> str:
    return """\
BLOCKED: You're in the writing-tests phase - only test files can be edited.
Write your failing test, then run it."""


def blocked_red(log_name: str) -> str:
    return f"""\
BLOCKED: Red confirmed. Log your Green declaration before editing.
Run (fill in the placeholders):

  uv run python -m scripts.tdd_log --log "{log_name}" green --change "what you plan to do" --file "path/to/file1.py" --file "path/to/file2.py" """


def blocked_test_in_green(log_name: str) -> str:
    return f"""\
BLOCKED: Test edits are not allowed during Green.
If you need to change your test, re-log your Red declaration first:

  uv run python -m scripts.tdd_log --log "{log_name}" red --test "path/to/test_file" --expects "test_name fails because ..." """


def blocked_green_not_listed(file_path: str, allowed: set[str], log_name: str) -> str:
    listed = "\n".join(f"  - {f}" for f in sorted(allowed)) if allowed else "  (none)"
    return f"""\
BLOCKED: {file_path} is not in your declared Green allowlist.
Declared files:
{listed}

To add it, re-run your Green declaration including this file:
  uv run python -m scripts.tdd_log --log "{log_name}" green --change "..." --file "{file_path}" """


# ---------------------------------------------------------------------------
# Per-agent log fallback chain
# ---------------------------------------------------------------------------


def _is_agent_log_finished(log_path: Path) -> bool:
    """Check if an agent log has been finished by SubagentStop."""
    if not log_path.exists():
        return True
    content = log_path.read_text()
    return "## FINISHED" in content


def _check_agent_logs(file_path: str, rel_path: str, kind: str) -> bool:
    """Check per-agent TDD logs for edit permission (fallback chain).

    When the parent log blocks an edit, this checks all active (non-finished)
    agent logs. If any agent log permits the edit, it returns True.
    """
    project_root = get_project_root()
    for agent_log_path in glob.glob(str(project_root / "tdd-agent-*.log")):
        agent_log = Path(agent_log_path)
        if _is_agent_log_finished(agent_log):
            continue
        agent_state = read_state(agent_log)
        if agent_state == "making_tests_pass":
            if kind == "test" and is_skip_red_green(agent_log):
                return True
            if kind == "prod":
                allowed = read_green_allowlist(agent_log)
                if rel_path in allowed:
                    return True
        elif agent_state == "writing_tests" and kind == "test":
            return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def log_edit(
    log_path: Path,
    file_path: str,
    kind: str,
    state: str,
    result: str,
) -> None:
    """Append an edit attempt to the TDD log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"[edit] {file_path} ({kind}) state={state} - {result}\n")


def main() -> None:
    input_data = json.load(sys.stdin)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(f"TDD Pre-edit error getting file_path from tool_input: {tool_input}")
        sys.exit(1)

    kind = classify_file(file_path)
    log_path = get_log_path(input_data)
    log_name = log_path.name
    state = read_state(log_path)

    # Normalize to project-relative for allowlist comparison
    rel_path = _to_project_relative(file_path)

    # e2e_test and other → allowed
    # Log modifications without blocking
    # Only force TDD at the unit, integration, and component level
    if kind in ("e2e_test", "other"):
        log_edit(log_path, file_path, kind, state, "ALLOWED")
        sys.exit(0)

    # Permission table:
    #   initial          → block all (test + prod)
    #   writing_tests    → test ok, prod blocked
    #   red              → block all (test + prod)
    #   making_tests_pass → test blocked (unless skip-red), prod in allowlist
    if state == "initial":
        if _check_agent_logs(file_path, rel_path, kind):
            log_edit(log_path, file_path, kind, state, "ALLOWED(agent)")
            sys.exit(0)
        log_edit(log_path, file_path, kind, state, "BLOCKED")
        print(blocked_initial(log_name), file=sys.stderr)
        sys.exit(2)
    elif state == "writing_tests":
        if kind == "prod":
            if _check_agent_logs(file_path, rel_path, kind):
                log_edit(log_path, file_path, kind, state, "ALLOWED(agent)")
                sys.exit(0)
            log_edit(log_path, file_path, kind, state, "BLOCKED")
            print(blocked_writing_tests_impl(), file=sys.stderr)
            sys.exit(2)
        # test file → allowed
        log_edit(log_path, file_path, kind, state, "ALLOWED")
        sys.exit(0)
    elif state == "red":
        if _check_agent_logs(file_path, rel_path, kind):
            log_edit(log_path, file_path, kind, state, "ALLOWED(agent)")
            sys.exit(0)
        log_edit(log_path, file_path, kind, state, "BLOCKED")
        print(blocked_red(log_name), file=sys.stderr)
        sys.exit(2)
    elif state == "making_tests_pass":
        if kind == "test":
            if is_skip_red_green(log_path):
                log_edit(log_path, file_path, kind, state, "ALLOWED")
                sys.exit(0)
            if _check_agent_logs(file_path, rel_path, kind):
                log_edit(log_path, file_path, kind, state, "ALLOWED(agent)")
                sys.exit(0)
            log_edit(log_path, file_path, kind, state, "BLOCKED")
            print(blocked_test_in_green(log_name), file=sys.stderr)
            sys.exit(2)
        allowed = read_green_allowlist(log_path)
        warn_large_allowlist(allowed)
        if rel_path not in allowed:
            if _check_agent_logs(file_path, rel_path, kind):
                log_edit(log_path, file_path, kind, state, "ALLOWED(agent)")
                sys.exit(0)
            log_edit(log_path, file_path, kind, state, "BLOCKED")
            print(
                blocked_green_not_listed(rel_path, allowed, log_name),
                file=sys.stderr,
            )
            sys.exit(2)
        log_edit(log_path, file_path, kind, state, "ALLOWED")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
