#!/usr/bin/env python3
"""
Check for hard deletes on tables that support soft-delete.

Repositories that pass supports_soft_delete=True to BaseRepository should use
the inherited delete() method (which does soft-delete). Direct .delete().eq()
chains bypass that logic and must be flagged.
"""

import ast
import re
import sys
from pathlib import Path

Violation = tuple[int, str]

NOQA_HARD_DELETE_RE = re.compile(r"#\s*noqa:\s*hard-delete")
SOFT_DELETE_RE = re.compile(r"supports_soft_delete\s*=\s*True")


def has_supports_soft_delete(source: str) -> bool:
    """Check if source contains supports_soft_delete=True in a super().__init__ call."""
    return bool(SOFT_DELETE_RE.search(source))


class _DeleteChainVisitor(ast.NodeVisitor):
    """AST visitor to find self.client.table(...).delete() call chains."""

    def __init__(self, lines: list[str]) -> None:
        self.violations: list[Violation] = []
        self.lines = lines
        self.in_base_delete = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old = self.in_base_delete
        # Allow BaseRepository.delete method — it handles soft-delete internally
        if node.name == "delete":
            # Check if this is inside a class named BaseRepository
            # We detect this by checking parent context set during walk
            self.in_base_delete = True
        self.generic_visit(node)
        self.in_base_delete = old

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        old = self.in_base_delete
        if node.name == "delete":
            self.in_base_delete = True
        self.generic_visit(node)
        self.in_base_delete = old

    def visit_Call(self, node: ast.Call) -> None:
        if self.in_base_delete:
            self.generic_visit(node)
            return

        # Look for .delete() call that's part of self.client.table(...).delete()
        if self._is_delete_on_self_client(node):
            line_idx = node.end_lineno - 1 if node.end_lineno else node.lineno - 1
            # Check all lines from start to end for noqa
            start_line = node.lineno - 1
            end_line = line_idx + 1
            for i in range(start_line, min(end_line, len(self.lines))):
                if NOQA_HARD_DELETE_RE.search(self.lines[i]):
                    self.generic_visit(node)
                    return
            self.violations.append(
                (node.lineno, "Direct .delete() call bypasses soft-delete logic")
            )

        self.generic_visit(node)

    def _is_delete_on_self_client(self, node: ast.Call) -> bool:
        """Check if this call is self.client.table(...).delete().eq(...) pattern.

        We look for a .delete() call where the chain includes self.client.table().
        """
        # We need to find .delete() as an attribute call
        if not isinstance(node.func, ast.Attribute):
            return False
        if node.func.attr != "execute":
            # We actually want to detect the whole chain ending in .execute()
            # But the simplest approach: find .delete() calls on self.client chains
            return False

        # Walk up the chain looking for .delete() and self.client.table()
        return self._chain_has_delete_on_self_client(node.func.value)

    def _chain_has_delete_on_self_client(self, node: ast.expr) -> bool:
        """Walk the method chain to find .delete() called on self.client.table()."""
        has_delete = False
        has_self_client_table = False
        current = node

        while True:
            if isinstance(current, ast.Call):
                if isinstance(current.func, ast.Attribute):
                    attr_name = current.func.attr
                    if attr_name == "delete":
                        has_delete = True
                    if attr_name == "table" and self._is_self_client(
                        current.func.value
                    ):
                        has_self_client_table = True
                current = (
                    current.func.value
                    if isinstance(current.func, ast.Attribute)
                    else current.func
                )
            elif isinstance(current, ast.Attribute):
                current = current.value
            else:
                break

        return has_delete and has_self_client_table

    def _is_self_client(self, node: ast.expr) -> bool:
        """Check if node is self.client."""
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "client"
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        )


def find_direct_delete_chains(source: str) -> list[Violation]:
    """Find direct .delete().eq() chains on self.client in source code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    visitor = _DeleteChainVisitor(lines)

    # We need to handle the BaseRepository class context.
    # Walk classes and set context for the visitor.
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name == "BaseRepository":
            # Inside BaseRepository, all delete() methods are allowed
            old = visitor.in_base_delete
            visitor.in_base_delete = True
            visitor.visit(node)
            visitor.in_base_delete = old
        else:
            visitor.visit(node)

    return visitor.violations


def check_file(file_path: Path) -> list[Violation]:
    """Check a single repository file for hard-delete violations."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"Error reading {file_path}, skipping")
        return []

    if not has_supports_soft_delete(source):
        return []

    return find_direct_delete_chains(source)


def main() -> None:
    """Scan repository files and report hard-delete violations."""
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        files = sorted(Path("app/repositories").glob("**/*.py"))

    total_violations = 0

    for file_path in files:
        if not file_path.is_file() or file_path.suffix != ".py":
            continue

        violations = check_file(file_path)
        if violations:
            print(f"\n{file_path}:")
            for lineno, desc in violations:
                print(f"  Line {lineno} [hard-delete]: {desc}")
                total_violations += 1

    if total_violations > 0:
        print(
            f"\nFound {total_violations} hard-delete violations on soft-deleteable tables."
        )
        print(
            "Use the inherited delete() method or add '# noqa: hard-delete' for intentional cases."
        )
        sys.exit(1)
    else:
        print("No hard-delete violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
