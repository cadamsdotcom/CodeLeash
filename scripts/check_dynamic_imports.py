#!/usr/bin/env python3
"""
Script to detect dynamic imports (imports not at module level).

This script enforces that all import statements must be at the top level of files,
preventing imports inside functions, methods, or conditional blocks.
"""

import ast
import sys
from pathlib import Path


class DynamicImportChecker(ast.NodeVisitor):
    """AST visitor to detect imports not at module level."""

    def __init__(self) -> None:
        self.imports_in_functions = []
        self.current_function: str | None = None
        self.in_type_checking = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        old_function = self.current_function
        self.current_function = f"class {node.name}"
        self.generic_visit(node)
        self.current_function = old_function

    def visit_If(self, node: ast.If) -> None:
        """Visit if statements - check for TYPE_CHECKING."""
        # Check if this is a TYPE_CHECKING block
        is_type_checking = False
        if (isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING") or (
            isinstance(node.test, ast.Attribute)
            and isinstance(node.test.value, ast.Name)
            and node.test.value.id == "typing"
            and node.test.attr == "TYPE_CHECKING"
        ):
            is_type_checking = True

        if is_type_checking:
            old_type_checking = self.in_type_checking
            self.in_type_checking = True
            self.generic_visit(node)
            self.in_type_checking = old_type_checking
        else:
            self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        if self.current_function and not self.in_type_checking:
            self.imports_in_functions.append(
                (
                    node.lineno,
                    f"import {', '.join(alias.name for alias in node.names)}",
                    self.current_function,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statements."""
        if self.current_function and not self.in_type_checking:
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            self.imports_in_functions.append(
                (node.lineno, f"from {module} import {names}", self.current_function)
            )
        self.generic_visit(node)


def check_file(file_path: Path) -> list[tuple[int, str, str]]:
    """Check a single Python file for dynamic imports."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        checker = DynamicImportChecker()
        checker.visit(tree)
        return checker.imports_in_functions
    except SyntaxError:
        print(f"Syntax error in {file_path}, skipping")
        return []
    except UnicodeDecodeError:
        print(f"Unicode decode error in {file_path}, skipping")
        return []


def main() -> None:
    """Main function."""
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        # Default to checking all Python files in app/ and scripts/
        files = []
        for pattern in ["app/**/*.py", "scripts/**/*.py"]:
            files.extend(Path(".").glob(pattern))

    total_violations = 0

    for file_path in files:
        if not file_path.is_file() or file_path.suffix != ".py":
            continue

        violations = check_file(file_path)
        if violations:
            print(f"\n{file_path}:")
            for line_no, import_stmt, function_name in violations:
                print(f"  Line {line_no}: {import_stmt} (in {function_name})")
                total_violations += 1

    if total_violations > 0:
        print(f"\nFound {total_violations} dynamic import violations.")
        print("All imports must be at the top level of the file.")
        print(
            "Consider refactoring to move imports to the top or use dependency injection."
        )
        sys.exit(1)
    else:
        print("No dynamic import violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
