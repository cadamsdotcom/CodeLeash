#!/usr/bin/env python3
"""
Check for em dashes (U+2014) in tracked files.

Em dashes can sneak into source code from copy-pasting rich text or LLM output.
This check flags them so they get replaced with standard ASCII alternatives.
"""

import subprocess
import sys

Violation = tuple[int, str]

WHITELIST: list[str] = [
    "scripts/check_emdashes.py",
    "tests/unit/scripts/test_check_emdashes.py",
]

EM_DASH = "\u2014"


def check_file_content(content: str) -> list[Violation]:
    """Scan lines for em dashes, returning (line_number, message) tuples."""
    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if EM_DASH in line:
            violations.append((lineno, f"Found em dash ({EM_DASH}). Use '-' instead."))
    return violations


def check_file(path: str, whitelist: list[str]) -> list[Violation]:
    """Check a single file for em dashes, skipping whitelisted and binary files."""
    if path in whitelist:
        return []
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return []
    except OSError:
        return []
    return check_file_content(content)


def get_tracked_files() -> list[str]:
    """Get list of git-tracked files."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> None:
    """Scan all tracked files for em dashes."""
    files = get_tracked_files()
    total_violations = 0

    for path in files:
        if path in WHITELIST:
            continue

        violations = check_file(path, WHITELIST)
        if violations:
            print(f"\n{path}:")
            for lineno, msg in violations:
                print(f"  Line {lineno} [em-dash]: {msg}")
            total_violations += len(violations)

    if total_violations > 0:
        print(f"\nFound {total_violations} em dash violations.")
        sys.exit(1)
    else:
        print("No em dash violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
