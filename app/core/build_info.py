"""Build information utilities."""

import os
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def get_commit_sha() -> str:
    """
    Get the current git commit SHA (first 6 characters).

    Tries multiple sources in order:
    1. Fast path for tests (pytest detection)
    2. GIT_COMMIT_SHA environment variable (set during build)
    3. Git command (for development environments)
    4. Fallback to "unset"

    Returns:
        str: The first 6 characters of the commit SHA, or "unset"
    """
    # Fast path for tests - avoid expensive subprocess
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "pytest"

    # First, try environment variable (set during build/deployment)
    commit_sha = os.getenv("GIT_COMMIT_SHA")
    if commit_sha:
        return commit_sha[:6] if len(commit_sha) > 6 else commit_sha

    # Second, try git command (for development environments)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=6", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        # Git command failed (not a git repo, git not installed, etc.)
        pass

    # Fallback
    return "unset"


@lru_cache(maxsize=1)
def get_build_info() -> dict[str, str]:
    """
    Get comprehensive build information.

    Returns:
        dict: Build information including commit SHA, environment, etc.
    """
    return {
        "commit_sha": get_commit_sha(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service_name": "codeleash",
        "service_version": "0.1.0",
    }
