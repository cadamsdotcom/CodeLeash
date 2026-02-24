#!/usr/bin/env python3
"""
Script to detect unused API routes in FastAPI application.

This script analyzes FastAPI route definitions and compares them with
API calls in the React frontend to identify routes that are not being used.
"""

import argparse
import ast
import importlib
import inspect
import os
import re
import sys
import traceback
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI


class RouteExtractor(ast.NodeVisitor):
    """AST visitor to extract FastAPI route definitions."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.routes: set[tuple[str, str]] = set()  # (method, path) tuples
        self.router_name = "router"  # Default router name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to find route decorators."""
        self._check_route_decorators(node.decorator_list)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions to find route decorators."""
        self._check_route_decorators(node.decorator_list)
        self.generic_visit(node)

    def _check_route_decorators(self, decorators: list[ast.expr]) -> None:
        """Extract routes from FastAPI decorators."""
        for decorator in decorators:
            route_info = self._parse_route_decorator(decorator)
            if route_info:
                method, path = route_info
                self.routes.add((method.upper(), path))

    def _parse_route_decorator(self, decorator: ast.expr) -> tuple[str, str] | None:
        """Parse a single decorator to extract route info."""
        # Handle @router.get("/path") style decorators
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                # e.g., @router.get("/path")
                method = decorator.func.attr
                if method in {
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                    "trace",
                }:
                    path = self._extract_path_from_args(decorator.args)
                    if path:
                        return method, path

        # Handle @router.get (without parentheses, but this is rare)
        elif isinstance(decorator, ast.Attribute):
            method = decorator.attr
            if method in {
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "options",
                "head",
                "trace",
            }:
                # This case is rare and would need path from function name or other source
                pass

        return None

    def _extract_path_from_args(self, args: list[ast.expr]) -> str | None:
        """Extract path string from decorator arguments."""
        if not args:
            return None

        first_arg = args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            return first_arg.value

        return None


def extract_all_routes(app_ref: str) -> dict[tuple[str, str], list[Path]]:
    """Extract all routes from the FastAPI application using dynamic imports."""
    routes: dict[tuple[str, str], list[Path]] = defaultdict(list)

    try:
        # Parse app reference
        module_name, app_attr = app_ref.split(":", 1)

        # Import the module
        print(f"Importing module: {module_name}")
        module = importlib.import_module(module_name)

        # Get the app object
        app = getattr(module, app_attr)
        print(f"Got app object: {app}")

        # Inspect the FastAPI app's router
        if not isinstance(app, FastAPI):
            raise RuntimeError(f"Object {app_ref} is not a FastAPI instance")

        # Extract routes from the app's router
        route_data = extract_routes_from_app(app)

        print(f"Found {len(route_data)} routes")
        for (method, path), source_info in route_data.items():
            routes[(method, path)].append(source_info)

        return routes

    except Exception as e:
        print(f"Error extracting routes: {e}")
        traceback.print_exc()
        raise RuntimeError(f"Could not extract routes from {app_ref}: {e}")


def is_framework_route(method: str, path: str, source_file: Path) -> bool:
    """Check if this is a framework-generated route that should be ignored."""

    # FastAPI built-in documentation routes
    framework_routes = {
        ("/openapi.json", "GET"),
        ("/docs", "GET"),
        ("/docs/oauth2-redirect", "GET"),
        ("/redoc", "GET"),
        ("/health", "GET"),  # Common health check endpoint
    }

    if (path, method) in framework_routes:
        return True

    # Check if route comes from FastAPI framework files
    if source_file and "fastapi" in str(source_file):
        return True

    # Check for static file routes (usually auto-mounted)
    if path.startswith("/static/") or path.startswith("/dist/"):
        return True

    # Health check patterns
    return path in ["/health", "/ping", "/status", "/ready", "/alive"]


def extract_routes_from_app(app: FastAPI) -> dict[tuple[str, str], Path]:
    """Extract routes directly from FastAPI app instance."""
    route_data = {}

    # Iterate through all routes in the app
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            # This is an APIRoute
            for method in route.methods:
                if method != "HEAD":  # Skip HEAD methods, they're auto-generated
                    path = route.path

                    # Skip root route / and framework routes
                    if path == "/":
                        continue

                    # Try to get the source file of the endpoint function
                    source_file = None
                    if hasattr(route, "endpoint") and route.endpoint:
                        try:
                            source_file = Path(inspect.getfile(route.endpoint))
                        except (TypeError, OSError):
                            source_file = Path("unknown")

                    # Skip framework routes
                    if not is_framework_route(
                        method, path, source_file or Path("unknown")
                    ):
                        route_data[(method, path)] = source_file or Path("unknown")

    return route_data


def extract_variable_api_paths(
    content: str,
) -> dict[str, list[tuple[int, list[str]]]]:
    """Extract variable assignments that contain API paths.

    Returns a dict mapping variable names to a list of (position, paths) tuples.
    Position tracks where the assignment occurs so fetch calls can be matched
    to the nearest preceding assignment of the same variable name.
    """
    variable_paths: dict[str, list[tuple[int, list[str]]]] = {}

    # Pattern 1: const/let/var name = '/path' or `path`
    simple_patterns = [
        r"(?:const|let|var)\s+(\w+)\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
        r"(?:const|let|var)\s+(\w+)\s*=\s*`([^`]*\/[^`]*)`",
    ]

    for pattern in simple_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            var_name, path = match.group(1), match.group(2)
            if not should_ignore_url(path):
                variable_paths.setdefault(var_name, []).append((match.start(), [path]))

    # Pattern 2: Extract all path literals from variable assignments containing ternaries.
    # This handles nested ternaries with any number of branches by finding the full
    # assignment (up to the semicolon) and then extracting all path-like literals from it.
    assignment_pattern = (
        r"(?:const|let|var)\s+(\w+)\s*=\s*((?:(?!(?:const|let|var)\s).)*?;\s*$)"
    )
    for match in re.finditer(assignment_pattern, content, re.MULTILINE | re.DOTALL):
        var_name = match.group(1)
        rhs = match.group(2)
        # Only process assignments that contain a ternary operator
        if "?" not in rhs:
            continue
        # Extract all string/template literal paths from the right-hand side
        paths = []
        for path_match in re.finditer(
            r"['\"`]([^'\"`]*\/[^'\"`]*)['\"`]|`([^`]*\/[^`]*)`", rhs
        ):
            path = path_match.group(1) or path_match.group(2)
            if path and not should_ignore_url(path):
                paths.append(path)
        if paths:
            variable_paths.setdefault(var_name, []).append((match.start(), paths))

    return variable_paths


def extract_api_calls_from_ts_file(file_path: Path) -> set[tuple[str, str]]:
    """Extract API calls from a TypeScript/TSX file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return set()

    api_calls = set()

    # First, extract all variable assignments that contain API paths
    variable_paths = extract_variable_api_paths(content)

    # Patterns to match various API call styles - both /api/ and direct routes
    patterns = [
        # fetch('/any/path') or fetch(`/any/path`) - any absolute path
        r"fetch\s*\(\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
        # fetch(`/path/${var}`) - template literals with variables
        r"fetch\s*\(\s*`([^`]*\/[^`]*)`",
        # href="/path" - for navigation links that might indicate backend routes
        r"href\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
        # href={`/path/${var}`} - JSX template literals
        r"href\s*=\s*\{\s*`([^`]*\/[^`]*)`\s*\}",
        # src="/path" or src={`/path`} - image and iframe sources
        r"src\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
        r"src\s*=\s*\{\s*`([^`]*\/[^`]*)`\s*\}",
        # action="/path" - form actions
        r"action\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
        # window.location.href assignments
        r"window\.location\.href\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
        # Template literal assignments
        r"window\.location\.href\s*=\s*`([^`]*\/[^`]*)`",
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            url = match.group(1)
            # Filter out external URLs and static assets
            if not should_ignore_url(url):
                # Try to determine HTTP method from context
                method = determine_http_method(content, match.start())
                # Normalize the path
                normalized_path = normalize_path(url)
                if normalized_path:
                    api_calls.add((method, normalized_path))

    # Now look for fetch calls that use variables: fetch(varName, ...)
    # Pattern: fetch(variable_name, { or fetch(variable_name)
    variable_fetch_pattern = r"fetch\s*\(\s*(\w+)\s*[,\)]"
    matches = re.finditer(variable_fetch_pattern, content, re.MULTILINE)
    for match in matches:
        var_name = match.group(1)
        # Check if this variable contains an API path
        if var_name in variable_paths:
            # Find the nearest preceding assignment for this variable name
            fetch_pos = match.start()
            best_pos = -1
            best_paths: list[str] = []
            for assign_pos, paths in variable_paths[var_name]:
                if assign_pos < fetch_pos and assign_pos > best_pos:
                    best_pos = assign_pos
                    best_paths = paths
            if not best_paths:
                continue
            # Try to determine HTTP method from context
            method = determine_http_method(content, match.start())
            # Add paths from the nearest preceding assignment only
            for path in best_paths:
                normalized_path = normalize_path(path)
                if normalized_path:
                    api_calls.add((method, normalized_path))

    return api_calls


def determine_http_method(content: str, position: int) -> str:
    """Determine HTTP method from context around the API call."""
    # Look backwards from the position to find method context
    start = max(0, position - 200)
    context = content[start : position + 100]

    # Look for method indicators
    if re.search(r'method:\s*[\'"`]POST[\'"`]', context, re.IGNORECASE):
        return "POST"
    elif re.search(r'method:\s*[\'"`]PUT[\'"`]', context, re.IGNORECASE):
        return "PUT"
    elif re.search(r'method:\s*[\'"`]DELETE[\'"`]', context, re.IGNORECASE):
        return "DELETE"
    elif re.search(r'method:\s*[\'"`]PATCH[\'"`]', context, re.IGNORECASE):
        return "PATCH"

    # Default to GET if no method specified
    return "GET"


def should_ignore_url(url: str) -> bool:
    """Check if URL should be ignored (external, static assets, etc.)."""
    # Ignore external URLs
    if url.startswith("http://") or url.startswith("https://"):
        return True

    # Ignore static assets
    static_extensions = [
        ".js",
        ".css",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
    ]
    if any(url.endswith(ext) for ext in static_extensions):
        return True

    # Ignore relative paths (we only want absolute paths starting with /)
    if not url.startswith("/"):
        return True

    # Ignore specific static paths
    static_paths = ["/static/", "/dist/", "/assets/"]
    return bool(any(path in url for path in static_paths))


def normalize_path(path: str) -> str | None:
    """Normalize path for comparison with route definitions."""
    if not path.startswith("/"):
        return None

    # Keep the path as-is, don't remove /api prefix since routes have it
    normalized = path

    # Handle template literal variables FIRST (before query parameter processing)
    # This prevents ${project?.id} from being split at the ? character

    # Handle template literal variables that are path parameters (in the path, not query string)
    # Only convert ${var} to {id} if it appears within path segments, not at the end
    # This handles cases like /api/users/${userId}/posts but not /api/users${queryParams}
    normalized = re.sub(r"/\$\{[^}]+\}", "/{id}", normalized)

    # Handle ${var} that appears at the end of a path (likely query params) - remove them
    normalized = re.sub(r"\$\{[^}]+\}$", "", normalized)

    # Now handle actual query parameters - remove them for comparison
    # This must come AFTER template literal processing to avoid splitting ${project?.id}
    if "?" in normalized:
        normalized = normalized.split("?")[0]

    # Handle common ID patterns in URLs
    normalized = re.sub(r"/\d+(?=/|$)", "/{id}", normalized)

    return normalized


def extract_all_api_calls() -> set[tuple[str, str]]:
    """Extract all API calls from React/TypeScript files."""
    api_calls = set()

    # Find all TypeScript/TSX files in src/
    ts_files = []
    for pattern in ["src/**/*.ts", "src/**/*.tsx"]:
        ts_files.extend(Path(".").glob(pattern))

    for file_path in ts_files:
        if file_path.is_file():
            file_calls = extract_api_calls_from_ts_file(file_path)
            api_calls.update(file_calls)

    return api_calls


def normalize_route_path(path: str) -> str:
    """Normalize route path for comparison."""
    # Handle common parameter patterns - normalize all path parameters to {id}
    normalized = re.sub(r"\{[^}]+\}", "{id}", path)
    return normalized


def find_unused_routes(app_ref: str) -> dict[tuple[str, str], list[Path]]:
    """Find routes that are not used by the frontend."""
    print("Extracting routes from FastAPI application...")
    all_routes = extract_all_routes(app_ref)

    print("Extracting API calls from React/TypeScript files...")
    all_api_calls = extract_all_api_calls()

    print(f"Found {len(all_routes)} routes and {len(all_api_calls)} API calls")

    # Optional debug output
    debug = os.getenv("DEBUG", False)
    if debug:  # Set to True for debugging
        print("\nAll API calls found with 'project':")
        for method, path in sorted(all_api_calls):
            if "project" in path:
                print(f"  {method} {path}")

        print("\nAll routes found with 'project':")
        for (method, path), _file_paths in sorted(all_routes.items()):
            if "project" in path:
                print(f"  {method} {path}")

    print(f"\nMatched {len(all_api_calls)} API calls against {len(all_routes)} routes")

    # Normalize paths for comparison
    normalized_api_calls = set()
    for method, path in all_api_calls:
        normalized_path = normalize_route_path(path)
        normalized_api_calls.add((method, normalized_path))

    unused_routes = {}
    for (method, path), file_paths in all_routes.items():
        normalized_path = normalize_route_path(path)

        # Skip certain routes that are used by infrastructure, not frontend
        if path == "/metrics":  # Prometheus metrics endpoint
            continue

        # Skip sample greetings API routes - JSON API endpoints, not called from frontend
        if path.startswith("/api/greetings"):
            continue

        # Check if this route is used
        is_used = False

        # Direct match
        if (method, normalized_path) in normalized_api_calls:
            is_used = True

        # Check with different HTTP methods (some APIs might use different methods)
        if not is_used:
            for _api_method, api_path in normalized_api_calls:
                if normalized_path == api_path:
                    is_used = True
                    break

        # Additional check: for routes that might be called from both web and API
        # Sometimes the route pattern might not match exactly
        if not is_used:
            # Check if any API call path contains this route path as a substring
            for _api_method, api_path in normalized_api_calls:
                if (path in api_path or api_path in path) and path_similarity(
                    normalized_path, api_path
                ) > 0.8:
                    # Fuzzy match for similar paths
                    is_used = True
                    break

        if not is_used:
            unused_routes[(method, path)] = file_paths

    return unused_routes


def path_similarity(path1: str, path2: str) -> float:
    """Calculate similarity between two paths."""
    if path1 == path2:
        return 1.0

    # Simple similarity based on common segments
    segments1 = [s for s in path1.split("/") if s]
    segments2 = [s for s in path2.split("/") if s]

    if not segments1 or not segments2:
        return 0.0

    common = 0
    max_len = max(len(segments1), len(segments2))

    for i in range(min(len(segments1), len(segments2))):
        if segments1[i] == segments2[i] or "{id}" in (segments1[i], segments2[i]):
            common += 1

    return common / max_len


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Check for unused API routes in FastAPI application"
    )
    parser.add_argument(
        "app_ref",
        nargs="?",
        default="main:app",
        help="App reference in format module:app_name (default: main:app)",
    )

    args = parser.parse_args()

    print(f"Checking for unused API routes from {args.app_ref}...")

    unused_routes = find_unused_routes(args.app_ref)

    if not unused_routes:
        print("No unused routes found.")
        return

    total_unused = 0
    for (method, path), file_paths in unused_routes.items():
        print(f"\nUnused route: {method} {path}")
        for file_path in file_paths:
            print(f"  Defined in: {file_path}")
        total_unused += 1

    print(f"\nFound {total_unused} unused routes.")
    print(
        "Consider removing these routes or verifying they are not used through other means."
    )

    # Exit with error code to fail CI if unused routes found
    sys.exit(1 if total_unused > 0 else 0)


if __name__ == "__main__":
    main()
