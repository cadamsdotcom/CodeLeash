"""Tests for tdd_common shared utilities."""

import pytest

from scripts.tdd_common import is_prod_file


class TestIsProdFile:
    """Tests for is_prod_file function."""

    @pytest.mark.parametrize(
        "path",
        [
            "src/components/Button.tsx",
            "src/utils/helpers.ts",
            "app/models/user.py",
            "app/routes/api.py",
            "scripts/tdd_common.py",
            "main.py",
            "worker.py",
        ],
    )
    def test_prod_files_are_detected(self, path: str) -> None:
        assert is_prod_file(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "tests/unit/test_foo.py",
            "tests/e2e/test_flow.py",
            "README.md",
            "pyproject.toml",
            ".gitignore",
            "CLAUDE.md",
            "package.json",
            "conftest.py",
        ],
    )
    def test_non_prod_files_are_not_detected(self, path: str) -> None:
        assert is_prod_file(path) is False
