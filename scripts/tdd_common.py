"""Shared utilities for TDD Guard hooks.

Hook lifecycle for Bash commands:
  - PostToolUse fires on exit 0 → logs SUCCEEDED
  - PostToolUseFailure fires on non-zero exit → logs FAILED (with exit code
    if available in the input schema, e.g. FAILED(1))
"""

import hashlib
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# File classification patterns (matched against project-relative paths)
# ---------------------------------------------------------------------------

PROD_PATTERNS = [
    r"^src/",
    r"^app/",
    r"^scripts/.*\.py$",
    r"^main\.py$",
]


def is_prod_file(rel_path: str) -> bool:
    """Check if a relative path is a production file."""
    return any(re.search(p, rel_path) for p in PROD_PATTERNS)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

STATES = {
    "initial": "initial",
    "writing_tests": "writing_tests",
    "red": "red",
    "making_tests_pass": "making_tests_pass",
}


def _find_preceding_declaration(lines: list[str], before_index: int) -> str | None:
    """Scan backwards from before_index to find the preceding Red/Green declaration."""
    for i in range(before_index - 1, -1, -1):
        stripped = lines[i].rstrip()
        if stripped.startswith("## Green"):
            return "green"
        if stripped.startswith("## Red"):
            return "red"
    return None


def read_state(log_path: Path) -> str:
    """Scan log bottom-up for the last significant line to derive state."""
    if not log_path.exists():
        return STATES["initial"]

    text = log_path.read_text()
    lines = text.strip().splitlines()

    # Walk backwards to find last significant line
    for i, line in enumerate(reversed(lines)):
        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped.startswith("[test]") and stripped.endswith("- SUCCEEDED"):
            return STATES["initial"]
        if stripped.startswith("[test]") and "- FAILED" in stripped:
            # Look further back for the preceding declaration
            preceding = _find_preceding_declaration(lines, len(lines) - 1 - i)
            if preceding == "green":
                return STATES["making_tests_pass"]
            return STATES["red"]
        if stripped.startswith("## Red"):
            return STATES["writing_tests"]
        if stripped.startswith("## Green"):
            return STATES["making_tests_pass"]
        # Skip other lines (Test:, Expects:, Change:, File:, [bash], [edit])

    return STATES["initial"]


def get_log_path(input_data: dict) -> Path:
    """Derive per-agent log path from transcript_path.

    Returns a relative path (e.g., tdd-abc123.log) since hooks run from
    the project root.
    """
    transcript = input_data.get("transcript_path", "")
    if transcript:
        key = hashlib.md5(transcript.encode()).hexdigest()[:8]
        return Path(f"tdd-{key}.log")
    return Path("tdd.log")
