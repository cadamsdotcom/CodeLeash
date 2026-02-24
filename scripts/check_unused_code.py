#!/usr/bin/env python3
"""
Script to detect unused functions and methods in Python code.

This script uses AST parsing to identify function and method definitions
that are never called anywhere in the codebase, with special handling for
FastAPI routes, dependency injection, and other common patterns.
"""

import ast
import re
import sys
import traceback
from collections import defaultdict
from pathlib import Path


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze function definitions and calls."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.definitions: set[str] = set()
        self.calls: set[str] = set()
        self.imports: set[str] = set()
        self.current_class: str | None = None
        self.route_functions: set[str] = (
            set()
        )  # Track functions that are route handlers
        self.variable_types: dict[str, str] = {}  # Track variable -> type mappings
        self.function_return_types: dict[str, str] = {}  # Track function -> return type
        self._current_function: str | None = None  # Track current function context
        self._source_lines: list[str] = []  # Cache source lines for comment checking

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        # Build fully qualified name
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = node.name

        # Check if this is a route function (has route decorators)
        is_route_function = self._is_route_function(node.decorator_list)
        if is_route_function:
            self.route_functions.add(func_name)

        # Skip magic methods and known patterns
        if self._should_skip_function(node.name, node.decorator_list):
            # Still track function context and visit children
            old_function = self._current_function
            self._current_function = node.name
            self.generic_visit(node)
            self._current_function = old_function
            return

        # Check for check_unused_code: ignore comment
        if self._has_noqa_comment(
            node.lineno, node.body[0].lineno if node.body else None
        ):
            # Still track function context and visit children
            old_function = self._current_function
            self._current_function = node.name
            self.generic_visit(node)
            self._current_function = old_function
            return

        self.definitions.add(func_name)

        # Track function context for return type analysis
        old_function = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        # Build fully qualified name
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = node.name

        # Check if this is a route function (has route decorators)
        is_route_function = self._is_route_function(node.decorator_list)
        if is_route_function:
            self.route_functions.add(func_name)

        # Skip magic methods and known patterns
        if self._should_skip_function(node.name, node.decorator_list):
            # Still track function context and visit children
            old_function = self._current_function
            self._current_function = node.name
            self.generic_visit(node)
            self._current_function = old_function
            return

        # Check for check_unused_code: ignore comment
        if self._has_noqa_comment(
            node.lineno, node.body[0].lineno if node.body else None
        ):
            # Still track function context and visit children
            old_function = self._current_function
            self._current_function = node.name
            self.generic_visit(node)
            self._current_function = old_function
            return

        self.definitions.add(func_name)

        # Track function context for return type analysis
        old_function = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_function

    def _should_skip_function(self, name: str, decorators: list[ast.expr]) -> bool:
        """Check if function should be skipped from unused analysis."""
        # Skip magic methods
        if name.startswith("__") and name.endswith("__"):
            return True

        # Skip test methods
        if name.startswith("test_"):
            return True

        # Skip functions that look like FastAPI dependency providers
        if name.startswith("get_") or name.startswith("create_"):
            return True

        # Skip metrics functions (used by external monitoring systems)
        if name == "dispatch":
            return True

        # Skip AST visitor methods (part of the pattern)
        if name.startswith("visit_"):
            return True

        # Skip model validation methods
        if name == "model_post_init":
            return True

        # Check for decorators that indicate the function is used by framework
        for decorator in decorators:
            if isinstance(decorator, ast.Attribute):
                # FastAPI route decorators (e.g., router.get, app.post)
                if decorator.attr in {
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                    "trace",
                }:
                    return True
            elif isinstance(decorator, ast.Name):
                # Various decorators that indicate framework usage
                if decorator.id in {
                    "property",
                    "cached_property",
                    "classmethod",
                    "staticmethod",
                    "app",
                    "router",
                    "depends",
                    "lru_cache",
                    "asynccontextmanager",
                }:
                    return True
            # Handle function calls as decorators (e.g., @app.get("/path"))
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr
                in {
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                    "trace",
                }
            ):
                # e.g., @router.get(), @app.post()
                return True
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id in {"depends", "lru_cache"}
            ):
                # e.g., @depends()
                return True

        return False

    def _has_noqa_comment(self, lineno: int, end_lineno: int | None = None) -> bool:
        """Check if any line in the range has a check_unused_code: ignore comment."""
        if not self._source_lines or lineno <= 0 or lineno > len(self._source_lines):
            return False

        last = min(end_lineno or lineno, len(self._source_lines))
        for i in range(lineno - 1, last):  # lineno is 1-based
            if "# check_unused_code: ignore" in self._source_lines[i].lower():
                return True
        return False

    def _is_route_function(self, decorators: list[ast.expr]) -> bool:
        """Check if function has route decorators (FastAPI route handlers)."""
        for decorator in decorators:
            if isinstance(decorator, ast.Attribute):
                # FastAPI route decorators (e.g., router.get, app.post)
                if decorator.attr in {
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                    "trace",
                }:
                    return True
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr
                in {
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                    "trace",
                }
            ):
                # e.g., @router.get(), @app.post()
                return True
        return False

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
            # Also add qualified names for service method calls
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                method_name = node.func.attr

                # Add the direct call pattern
                self.calls.add(f"{var_name}.{method_name}")

                # If we know the variable's type, add the class.method pattern
                if var_name in self.variable_types:
                    class_name = self.variable_types[var_name]
                    self.calls.add(f"{class_name}.{method_name}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name references (includes function references passed as arguments)."""
        # Only count names that are being loaded (referenced), not stored (assigned to)
        if isinstance(node.ctx, ast.Load):
            self.calls.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute references (e.g. self.method passed as a callback)."""
        # Track attribute names used in load context (not just direct calls)
        if isinstance(node.ctx, ast.Load):
            self.calls.add(node.attr)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment statements to track variable types."""
        # Handle simple assignments like: var = func()
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id

            # Check if assignment is a function call that returns a class instance
            if isinstance(node.value, ast.Call) and isinstance(
                node.value.func, ast.Name
            ):
                func_name = node.value.func.id
                # Look up the return type of this function
                if func_name in self.function_return_types:
                    self.variable_types[var_name] = self.function_return_types[
                        func_name
                    ]
                else:
                    # Direct class instantiation: var = ClassName(...)
                    # Assume the function name is the class name (common pattern)
                    self.variable_types[var_name] = func_name

        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        """Visit return statements to track function return types."""
        # Only track returns within function definitions
        if (
            hasattr(self, "_current_function")
            and self._current_function
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
        ):
            # return ClassName(...)
            class_name = node.value.func.id
            self.function_return_types[self._current_function] = class_name

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)


def analyze_file(
    file_path: Path,
) -> tuple[set[str], set[str], set[str], set[str], dict[str, str], dict[str, str]]:
    """Analyze a single Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        analyzer = CodeAnalyzer(file_path)
        # Cache source lines for comment checking
        analyzer._source_lines = content.splitlines()

        try:
            analyzer.visit(tree)
        except Exception as e:
            print(f"Error during AST visit: {e}")
            traceback.print_exc()

        return (
            analyzer.definitions,
            analyzer.calls,
            analyzer.imports,
            analyzer.route_functions,
            analyzer.variable_types,
            analyzer.function_return_types,
        )
    except SyntaxError:
        print(f"Syntax error in {file_path}, skipping")
        return set(), set(), set(), set(), {}, {}
    except UnicodeDecodeError:
        print(f"Unicode decode error in {file_path}, skipping")
        return set(), set(), set(), set(), {}, {}


def _extract_service_dependencies(calls: set[str]) -> set[str]:
    """Extract service method calls that indicate dependency injection usage."""
    service_calls = set()
    for call in calls:
        # Look for service method calls (e.g., auth_service.authenticate_user)
        if "." in call:
            parts = call.split(".")
            if len(parts) == 2 and parts[0].endswith("_service"):
                service_calls.add(parts[1])  # Add the method name
        # Also look for direct calls to dependency providers
        if call.startswith("get_") and "_service" in call:
            # This suggests the service is being injected
            service_name = call.replace("get_", "").replace("_service", "")
            service_calls.add(f"*{service_name}")  # Mark as service pattern
    return service_calls


def find_unused_functions(python_files: list[Path]) -> dict[Path, list[str]]:
    """Find unused functions across all Python files."""
    all_definitions: dict[str, list[Path]] = defaultdict(list)
    all_calls: set[str] = set()
    file_specific_calls: dict[Path, set[str]] = {}
    service_dependencies: set[str] = set()
    all_function_return_types: dict[str, str] = {}
    all_variable_types: dict[str, str] = {}

    # First pass: collect all definitions, calls, and type information
    for file_path in python_files:
        (
            definitions,
            calls,
            imports,
            route_functions,
            variable_types,
            function_return_types,
        ) = analyze_file(file_path)

        # Track where each function is defined
        for func in definitions:
            all_definitions[func].append(file_path)

        # Collect all calls
        all_calls.update(calls)
        file_specific_calls[file_path] = calls

        # Imports might be used dynamically
        all_calls.update(imports)

        # Collect type information across all files
        all_function_return_types.update(function_return_types)
        all_variable_types.update(variable_types)

        # Detect service dependencies from files that have route functions
        if route_functions:  # Only extract service deps from files with actual routes
            service_dependencies.update(_extract_service_dependencies(calls))

    # Second pass: resolve cross-file type information
    # For each variable assignment, try to resolve its type using global function return types
    additional_calls = set()
    for file_path in python_files:
        variable_types, _ = analyze_file(file_path)[4:6]
        for var_name, var_type in variable_types.items():
            # If var_type is a function name, look up its return type
            if var_type in all_function_return_types:
                resolved_type = all_function_return_types[var_type]
                # Re-scan for calls to this variable and add class.method calls
                content = file_path.read_text(encoding="utf-8")
                # Find patterns like var_name.method_name()
                pattern = rf"\b{re.escape(var_name)}\.(\w+)\s*\("
                for match in re.finditer(pattern, content):
                    method_name = match.group(1)
                    additional_calls.add(f"{resolved_type}.{method_name}")

    all_calls.update(additional_calls)

    # Third pass: find unused functions
    unused_by_file: dict[Path, list[str]] = defaultdict(list)

    for func_name, file_paths in all_definitions.items():
        # Check if function is called anywhere
        is_used = False

        # Direct name match
        if func_name in all_calls:
            is_used = True

        # For standalone functions (no class prefix), check if base name is called
        if "." not in func_name and func_name in all_calls:
            is_used = True

        # Check method name without class prefix
        if "." in func_name:
            method_name = func_name.split(".", 1)[1]
            if method_name in all_calls:
                is_used = True
            # Check if this method is used by service dependency injection
            if method_name in service_dependencies:
                is_used = True

        # Check if it's a base class method that might be called via inheritance
        if "." in func_name:
            _class_name, method_name = func_name.split(".", 1)
            if f"super().{method_name}" in str(all_calls):
                is_used = True

        # Special case: check if function is used within its own file
        # (handles local helper functions)
        if not is_used:
            for file_path in file_paths:
                if func_name in file_specific_calls.get(file_path, set()):
                    is_used = True
                    break
                # Also check base name for standalone functions
                if "." not in func_name and func_name in file_specific_calls.get(
                    file_path, set()
                ):
                    is_used = True
                    break

        if not is_used:
            for file_path in file_paths:
                unused_by_file[file_path].append(func_name)

    return unused_by_file


def main() -> None:
    """Main function."""
    # Files to exclude from analysis
    EXCLUDED_FILES = {
        ".vulture_whitelist.py",  # Vulture whitelist file
    }

    # Find all Python files in app/, scripts/, and root directory
    python_files = []
    for pattern in ["app/**/*.py", "scripts/**/*.py", "*.py"]:
        python_files.extend(Path(".").glob(pattern))

    # Filter to actual Python files, excluding specific files
    python_files = [
        f
        for f in python_files
        if f.is_file() and f.suffix == ".py" and f.name not in EXCLUDED_FILES
    ]

    if not python_files:
        print("No Python files found to analyze.")
        return

    print(f"Analyzing {len(python_files)} Python files...")

    unused_functions = find_unused_functions(python_files)

    if not unused_functions:
        print("No unused functions found.")
        return

    total_unused = 0
    for file_path, unused_funcs in unused_functions.items():
        if unused_funcs:
            print(f"\n{file_path}:")
            for func in sorted(unused_funcs):
                print(f"  {func}")
                total_unused += 1

    print(
        f"\nFound {total_unused} unused functions across {len(unused_functions)} files."
    )
    print(
        "Consider removing these functions or verifying they are not used dynamically."
    )

    # Exit with error code to fail CI if unused functions found
    sys.exit(1 if total_unused > 0 else 0)


if __name__ == "__main__":
    main()
