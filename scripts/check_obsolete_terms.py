#!/usr/bin/env python3
"""
Check for obsolete terms in filenames and file content.

Prevents renamed terminology from creeping back into the codebase.
Files where old terms are expected (e.g., migrations) are whitelisted per-term.
"""

import re
import subprocess
import sys
from dataclasses import dataclass, field

Violation = tuple[int, str]


@dataclass
class ObsoleteTerm:
    term: str
    pattern: re.Pattern[str]
    replacement: str
    whitelist: list[str] = field(default_factory=list)


OBSOLETE_TERMS: list[ObsoleteTerm] = [
    ObsoleteTerm(
        term="dodo",
        pattern=re.compile(r"dodo", re.IGNORECASE),
        replacement="greeting",
        whitelist=[
            "scripts/check_obsolete_terms.py",
            "tests/unit/scripts/test_check_obsolete_terms.py",
        ],
    ),
]


def is_whitelisted(path: str, whitelist: list[str]) -> bool:
    """Check if a file path is in the whitelist."""
    return path in whitelist


def check_filename(path: str, term: ObsoleteTerm) -> str | None:
    """Check if a filename contains an obsolete term. Returns message or None."""
    if term.pattern.search(path):
        return f"Found obsolete term '{term.term}' in filename. Use '{term.replacement}' instead."
    return None


def check_file_content(content: str, term: ObsoleteTerm) -> list[Violation]:
    """Check file content for an obsolete term, returning (line_number, message) tuples."""
    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if term.pattern.search(line):
            violations.append(
                (
                    lineno,
                    f"Found obsolete term '{term.term}'. Use '{term.replacement}' instead.",
                )
            )
    return violations


def check_file(path: str, term: ObsoleteTerm) -> list[Violation]:
    """Check a single file for an obsolete term, handling whitelist and binary files."""
    if is_whitelisted(path, term.whitelist):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return []
    except OSError:
        return []
    return check_file_content(content, term)


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
    """Scan all tracked files for obsolete terms."""
    files = get_tracked_files()
    total_violations = 0

    for path in files:
        file_violations: list[str] = []

        for term in OBSOLETE_TERMS:
            if is_whitelisted(path, term.whitelist):
                continue

            # Check filename
            filename_msg = check_filename(path, term)
            if filename_msg:
                file_violations.append(f"  Filename [obsolete-term]: {filename_msg}")

            # Check content
            for lineno, msg in check_file(path, term):
                file_violations.append(f"  Line {lineno} [obsolete-term]: {msg}")

        if file_violations:
            print(f"\n{path}:")
            for v in file_violations:
                print(v)
            total_violations += len(file_violations)

    if total_violations > 0:
        print(f"\nFound {total_violations} obsolete term violations.")
        sys.exit(1)
    else:
        print("No obsolete term violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
