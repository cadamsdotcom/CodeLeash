"""TDD Guard - PostToolUse / PostToolUseFailure hook for Bash.

Logs bash commands to the per-agent TDD log.

Usage:
  PostToolUse (exit 0):         uv run python -m scripts.tdd_post_bash
  PostToolUseFailure (non-zero): uv run python -m scripts.tdd_post_bash --failed
"""

import json
import re
import sys
from pathlib import Path

from .tdd_common import get_log_path

E2E_CMD_PATTERN = re.compile(r"^npm run test:e2e")
TEST_CMD_PATTERN = re.compile(r"^npm (test( |$)|run test)")


def _is_tdd_log_write(log_path: Path, command: str) -> bool:
    """Check if a command is writing to the TDD log itself."""
    return str(log_path.name) in command


def main() -> None:
    failure_mode = "--failed" in sys.argv

    input_data = json.load(sys.stdin)

    command = input_data.get("tool_input", {}).get("command", "")

    log_path = get_log_path(input_data)
    if _is_tdd_log_write(log_path, command):
        sys.exit(0)

    command_single_line = command.replace("\n", "\\n")
    if E2E_CMD_PATTERN.search(command):
        tag = "ignored e2e test"
    elif TEST_CMD_PATTERN.search(command):
        tag = "test"
    else:
        tag = "bash"

    if failure_mode:
        error = input_data.get("error", "").strip()
        first_line = error.partition("\n")[0]
        suffix = f"FAILED({first_line})" if first_line else "FAILED"
    else:
        suffix = "SUCCEEDED"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"[{tag}] {command_single_line} - {suffix}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
