#!/usr/bin/env python3
"""
Check frontend code quality.

Current checks:
1. No <p> nesting inside Radix Dialog/AlertDialog Description (renders as <p>)
   - use asChild with <div> wrapper, or replace <p> with <span className="block">
"""

import re
import sys
from pathlib import Path

Violation = tuple[int, str, str]

DESCRIPTION_OPEN_RE = re.compile(r"<(AlertDialog|Dialog)\.Description\b")
DESCRIPTION_CLOSE_RE = re.compile(r"</(AlertDialog|Dialog)\.Description>")
AS_CHILD_RE = re.compile(r"\basChild\b")
PARAGRAPH_TAG_RE = re.compile(r"<p[\s>/]")
TAG_END_RE = re.compile(r"(?<!/)>")
SELF_CLOSING_TAG_RE = re.compile(r"/\s*>")


def _check_dialog_description_nesting(source: str) -> list[Violation]:
    """Find <p> tags nested inside Description without asChild."""
    lines = source.splitlines()
    violations: list[Violation] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        open_match = DESCRIPTION_OPEN_RE.search(line)
        if not open_match:
            i += 1
            continue

        # Collect the full opening tag (may span multiple lines)
        tag_lines = [line]
        # Check if the tag closes on this line
        rest_of_line = line[open_match.start() :]
        while not TAG_END_RE.search(rest_of_line) and not SELF_CLOSING_TAG_RE.search(
            rest_of_line
        ):
            i += 1
            if i >= len(lines):
                break
            tag_lines.append(lines[i])
            rest_of_line = lines[i]

        full_tag = "\n".join(tag_lines)

        # Self-closing tag - no children possible
        if SELF_CLOSING_TAG_RE.search(full_tag):
            i += 1
            continue

        # Has asChild - children render under a different element
        if AS_CHILD_RE.search(full_tag):
            # Skip to closing tag
            i += 1
            while i < len(lines):
                if DESCRIPTION_CLOSE_RE.search(lines[i]):
                    break
                i += 1
            i += 1
            continue

        # Scan content until closing tag for <p> elements
        i += 1
        while i < len(lines):
            if DESCRIPTION_CLOSE_RE.search(lines[i]):
                break
            if PARAGRAPH_TAG_RE.search(lines[i]):
                violations.append(
                    (
                        i + 1,  # 1-indexed line number
                        "dialog-p-nesting",
                        '<p> inside Description (renders as <p>) - use asChild with <div>, or <span className="block">',
                    )
                )
            i += 1
        i += 1

    return violations


def check_source(source: str, filename: str) -> list[Violation]:
    """Check source for all applicable frontend violations."""
    violations: list[Violation] = []
    violations.extend(_check_dialog_description_nesting(source))
    return violations


def check_file(file_path: Path) -> list[Violation]:
    """Check a single file for violations."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return check_source(source, str(file_path))


def main() -> None:
    """Scan frontend source files and report violations."""
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        files = sorted(Path("src").glob("**/*.tsx"))

    total = 0
    for fp in files:
        if not fp.is_file():
            continue
        violations = check_file(fp)
        if violations:
            print(f"\n{fp}:")
            for lineno, vtype, desc in violations:
                print(f"  Line {lineno} [{vtype}]: {desc}")
                total += 1

    if total > 0:
        print(f"\nFound {total} frontend code quality violations.")
        sys.exit(1)
    else:
        print("No frontend code quality violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
