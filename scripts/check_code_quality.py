#!/usr/bin/env python3
"""
Check code quality across the codebase.

Enforces zero-tolerance rules:
1. No page.wait_for_timeout() calls in e2e tests - use polling utilities or Playwright built-in waiting
2. No if/else branches in e2e test_* methods - tests should fully control system state
3. No repository.client access outside repository files - use repository methods instead
"""

import ast
import re
import sys
from pathlib import Path

# Violation tuple: (line_number, violation_type, description)
Violation = tuple[int, str, str]

WAIT_FOR_TIMEOUT_RE = re.compile(r"^([^#]*?)wait_for_timeout\(")
NOQA_FIXED_WAIT_RE = re.compile(r"#\s*noqa:\s*fixed-wait")
NOQA_CONDITIONAL_RE = re.compile(r"#\s*noqa:\s*conditional")
NOQA_MOCK_SPEC_BYPASS_RE = re.compile(r"#\s*noqa:\s*mock-spec-bypass")
REPOSITORY_CLIENT_RE = re.compile(r"^([^#]*?)repository\.client\b")

# Files where repository.client checks do NOT apply
_REPOSITORY_CLIENT_SKIP_PREFIXES = (
    "app/repositories/",
    "tests/",
    "app/core/container.py",
)


def _check_repository_client_access(source: str) -> list[Violation]:
    """Find repository.client access outside repository files."""
    violations = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if REPOSITORY_CLIENT_RE.search(line):
            violations.append(
                (
                    lineno,
                    "repository-client",
                    "Access database through repository methods instead of repository.client",
                )
            )
    return violations


def _check_fixed_waits(source: str) -> list[Violation]:
    """Find wait_for_timeout() calls that are not in comments and not suppressed."""
    violations = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if WAIT_FOR_TIMEOUT_RE.search(line) and not NOQA_FIXED_WAIT_RE.search(line):
            violations.append(
                (
                    lineno,
                    "fixed-wait",
                    "Use polling utilities or Playwright built-in waiting instead of wait_for_timeout()",
                )
            )
    return violations


def _is_if_name_main(node: ast.If) -> bool:
    """Check if an If node is `if __name__ == '__main__':`."""
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _check_conditionals(source: str) -> list[Violation]:
    """Find if statements inside test_* functions using AST analysis."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue

        # Walk the function body looking for If nodes
        for child in ast.walk(node):
            if not isinstance(child, ast.If):
                continue
            if _is_if_name_main(child):
                continue
            # Check noqa suppression on the line
            line_idx = child.lineno - 1
            if line_idx < len(lines) and NOQA_CONDITIONAL_RE.search(lines[line_idx]):
                continue
            violations.append(
                (
                    child.lineno,
                    "conditional",
                    "Avoid if/else branches in test methods - tests should control state directly",
                )
            )

    return violations


def _check_mock_spec_bypass(source: str) -> list[Violation]:
    """Find attribute assignments on spec-based mocks using AST analysis."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    violations = []

    # Track which variables are Mock objects with spec parameter
    spec_mocks = set()

    # Find Mock(spec=...) assignments
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        # Check if RHS is a Call to Mock with spec kwarg
        if not isinstance(node.value, ast.Call):
            continue

        # Check if it's Mock or MagicMock
        is_mock_call = False
        if (
            isinstance(node.value.func, ast.Name)
            and node.value.func.id
            in (
                "Mock",
                "MagicMock",
            )
        ) or (
            isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr
            in (
                "Mock",
                "MagicMock",
            )
        ):
            is_mock_call = True

        if not is_mock_call:
            continue

        # Check if spec is in keywords
        has_spec = any(kw.arg == "spec" for kw in node.value.keywords)
        if not has_spec:
            continue

        # Track the variable names
        for target in node.targets:
            if isinstance(target, ast.Name):
                spec_mocks.add(target.id)

    # Find attribute assignments on tracked spec mocks
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        # Check if LHS is an attribute access on a spec mock
        for target in node.targets:
            if not isinstance(target, ast.Attribute):
                continue
            if not isinstance(target.value, ast.Name):
                continue
            if target.value.id not in spec_mocks:
                continue

            # Check noqa suppression on the line
            line_idx = node.lineno - 1
            if line_idx < len(lines) and NOQA_MOCK_SPEC_BYPASS_RE.search(
                lines[line_idx]
            ):
                continue

            violations.append(
                (
                    node.lineno,
                    "mock-spec-bypass",
                    "Attribute assignment on spec-based mock bypasses spec validation - use configure_mock() or create_autospec()",
                )
            )

    return violations


def check_source(source: str, filename: str) -> list[Violation]:
    """Check a source string for applicable violation types based on filename."""
    violations = []
    # E2e checks only apply to e2e test files
    if "tests/e2e" in filename:
        violations.extend(_check_fixed_waits(source))
        violations.extend(_check_conditionals(source))
    # Mock spec bypass check applies to all test files
    if filename.startswith("tests/") or filename.startswith("test_"):
        violations.extend(_check_mock_spec_bypass(source))
    # Repository client check applies to app files outside repositories
    if not any(filename.startswith(p) for p in _REPOSITORY_CLIENT_SKIP_PREFIXES):
        violations.extend(_check_repository_client_access(source))
    return violations


def check_file(file_path: Path) -> list[Violation]:
    """Check a single file for violations."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"Error reading {file_path}, skipping")
        return []
    return check_source(source, str(file_path))


def _collect_files() -> list[Path]:
    """Collect all files to check: e2e tests and app code (excluding repositories)."""
    files: list[Path] = []
    files.extend(sorted(Path("tests/e2e").glob("**/*.py")))
    for p in sorted(Path("app").glob("**/*.py")):
        if not str(p).startswith("app/repositories/"):
            files.append(p)
    return files


def main() -> None:
    """Scan source files and report violations."""
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        files = _collect_files()

    total_violations = 0

    for file_path in files:
        if not file_path.is_file() or file_path.suffix != ".py":
            continue

        violations = check_file(file_path)
        if violations:
            print(f"\n{file_path}:")
            for lineno, vtype, desc in violations:
                print(f"  Line {lineno} [{vtype}]: {desc}")
                total_violations += 1

    if total_violations > 0:
        print(f"\nFound {total_violations} code quality violations.")
        sys.exit(1)
    else:
        print("No code quality violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
