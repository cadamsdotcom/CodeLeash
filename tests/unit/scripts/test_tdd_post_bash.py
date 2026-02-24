"""Tests for command classification in tdd_post_bash."""

from scripts.tdd_post_bash import E2E_CMD_PATTERN, TEST_CMD_PATTERN


def _classify(command: str) -> str:
    """Classify a command the same way main() does."""
    if E2E_CMD_PATTERN.search(command):
        return "ignored e2e test"
    if TEST_CMD_PATTERN.search(command):
        return "test"
    return "bash"


class TestCommandClassification:
    """TEST_CMD_PATTERN must recognise all test runners."""

    def test_npm_test(self) -> None:
        assert _classify("npm test") == "test"

    def test_npm_run_test(self) -> None:
        assert _classify("npm run test") == "test"

    def test_npm_test_with_args(self) -> None:
        assert _classify("npm test -- --watch") == "test"

    def test_uv_run_pytest_is_bash(self) -> None:
        assert _classify("uv run pytest tests/unit/") == "bash"

    def test_pytest_bare_is_bash(self) -> None:
        assert _classify("pytest tests/unit/services/") == "bash"

    def test_npx_vitest_is_bash(self) -> None:
        assert _classify("npx vitest run src/pages/ProjectWizard.test.tsx") == "bash"

    def test_vitest_bare_is_bash(self) -> None:
        assert _classify("vitest run src/pages/ProjectWizard.test.tsx") == "bash"

    def test_node_modules_vitest_is_bash(self) -> None:
        assert _classify("./node_modules/.bin/vitest run src/") == "bash"

    def test_e2e_ignored(self) -> None:
        assert _classify("npm run test:e2e tests/e2e/test_foo.py") == "ignored e2e test"

    def test_git_status_is_bash(self) -> None:
        assert _classify("git status") == "bash"

    def test_ls_is_bash(self) -> None:
        assert _classify("ls") == "bash"
