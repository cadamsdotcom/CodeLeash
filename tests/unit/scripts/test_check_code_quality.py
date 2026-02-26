"""Tests for check_code_quality.py - code quality checks across the codebase."""

from scripts.check_code_quality import check_source


class TestFixedWaitDetection:
    """Detect page.wait_for_timeout() calls in e2e tests."""

    def test_counts_wait_for_timeout_calls(self) -> None:
        source = (
            "def test_something(page):\n"
            "    page.wait_for_timeout(1000)\n"
            "    page.click('button')\n"
            "    page.wait_for_timeout(500)\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        fixed_wait_violations = [v for v in violations if v[1] == "fixed-wait"]
        assert len(fixed_wait_violations) == 2

    def test_fixed_wait_noqa_exclusion(self) -> None:
        source = (
            "def test_something(page):\n"
            "    page.wait_for_timeout(1000)  # noqa: fixed-wait\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        fixed_wait_violations = [v for v in violations if v[1] == "fixed-wait"]
        assert len(fixed_wait_violations) == 0

    def test_fixed_wait_in_comment_ignored(self) -> None:
        source = (
            "def test_something(page):\n"
            "    # page.wait_for_timeout(1000)\n"
            "    pass\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        fixed_wait_violations = [v for v in violations if v[1] == "fixed-wait"]
        assert len(fixed_wait_violations) == 0


class TestConditionalDetection:
    """Detect if/else branches in test_* methods."""

    def test_counts_if_statements_in_test_methods(self) -> None:
        source = (
            "def test_something(page):\n"
            "    if page.is_visible('button'):\n"
            "        page.click('button')\n"
            "    if True:\n"
            "        pass\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        conditional_violations = [v for v in violations if v[1] == "conditional"]
        assert len(conditional_violations) == 2

    def test_ignores_fixture_conditionals(self) -> None:
        source = (
            "import pytest\n"
            "@pytest.fixture\n"
            "def my_fixture():\n"
            "    if True:\n"
            "        return 'a'\n"
            "    return 'b'\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        conditional_violations = [v for v in violations if v[1] == "conditional"]
        assert len(conditional_violations) == 0

    def test_ignores_helper_conditionals(self) -> None:
        source = (
            "def helper_function():\n"
            "    if True:\n"
            "        return 'a'\n"
            "    return 'b'\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        conditional_violations = [v for v in violations if v[1] == "conditional"]
        assert len(conditional_violations) == 0

    def test_ignores_if_name_main(self) -> None:
        source = (
            "def test_something(page):\n"
            "    pass\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    pass\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        conditional_violations = [v for v in violations if v[1] == "conditional"]
        assert len(conditional_violations) == 0

    def test_plain_print_does_not_suppress_violation(self) -> None:
        source = (
            "def test_something(page):\n"
            "    if page.locator('x').count() > 0:\n"
            '        print("found x")\n'
            "        page.click('x')\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        conditional_violations = [v for v in violations if v[1] == "conditional"]
        assert len(conditional_violations) == 1

    def test_conditional_noqa_exclusion(self) -> None:
        source = (
            "def test_something(page):\n"
            "    if page.is_visible('button'):  # noqa: conditional\n"
            "        page.click('button')\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        conditional_violations = [v for v in violations if v[1] == "conditional"]
        assert len(conditional_violations) == 0


class TestRepositoryClientDetection:
    """Detect repository.client access outside repository files."""

    def test_flags_repository_client_access(self) -> None:
        source = (
            "class ProjectService:\n"
            "    def get_data(self):\n"
            "        self.repository.client.table('projects').select('*').execute()\n"
        )
        violations = check_source(source, "app/services/project.py")
        rc_violations = [v for v in violations if v[1] == "repository-client"]
        assert len(rc_violations) == 1

    def test_flags_named_repository_client_access(self) -> None:
        source = (
            "class ReviewService:\n"
            "    def get_client(self):\n"
            "        return self.review_repository.client\n"
        )
        violations = check_source(source, "app/services/review.py")
        rc_violations = [v for v in violations if v[1] == "repository-client"]
        assert len(rc_violations) == 1

    def test_ignores_repository_client_in_comments(self) -> None:
        source = (
            "class ProjectService:\n"
            "    def get_data(self):\n"
            "        # self.repository.client.table('projects')\n"
            "        pass\n"
        )
        violations = check_source(source, "app/services/project.py")
        rc_violations = [v for v in violations if v[1] == "repository-client"]
        assert len(rc_violations) == 0

    def test_skipped_for_repository_files(self) -> None:
        source = (
            "class ProjectRepository:\n"
            "    def get_data(self):\n"
            "        self.repository.client.table('projects').select('*').execute()\n"
        )
        violations = check_source(source, "app/repositories/project.py")
        rc_violations = [v for v in violations if v[1] == "repository-client"]
        assert len(rc_violations) == 0

    def test_skipped_for_test_files(self) -> None:
        source = (
            "class TestSomething:\n"
            "    def test_it(self):\n"
            "        self.repository.client.table('projects').select('*').execute()\n"
        )
        violations = check_source(source, "tests/unit/test_something.py")
        rc_violations = [v for v in violations if v[1] == "repository-client"]
        assert len(rc_violations) == 0

    def test_skipped_for_container_file(self) -> None:
        source = "client = get_supabase_service_client()\nrepository.client\n"
        violations = check_source(source, "app/core/container.py")
        rc_violations = [v for v in violations if v[1] == "repository-client"]
        assert len(rc_violations) == 0


class TestIntegration:
    """Integration behavior for overall pass/fail."""

    def test_zero_violations_passes(self) -> None:
        source = (
            "def test_something(page):\n"
            "    page.click('button')\n"
            "    expect(page.locator('div')).to_be_visible()\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        assert len(violations) == 0

    def test_any_violation_fails(self) -> None:
        source = "def test_something(page):\n" "    page.wait_for_timeout(500)\n"
        violations = check_source(source, "tests/e2e/test_example.py")
        assert len(violations) > 0

    def test_reports_both_violation_types(self) -> None:
        source = (
            "def test_something(page):\n"
            "    page.wait_for_timeout(500)\n"
            "    if page.is_visible('x'):\n"
            "        pass\n"
        )
        violations = check_source(source, "tests/e2e/test_example.py")
        types = {v[1] for v in violations}
        assert "fixed-wait" in types
        assert "conditional" in types


class TestMockSpecBypass:
    """Detect attribute assignments on spec-based mocks."""

    def test_flags_attribute_assignment_on_spec_mock(self) -> None:
        source = (
            "from unittest.mock import Mock, AsyncMock\n"
            "mock_obj = Mock(spec=SomeClass)\n"
            "mock_obj.method = AsyncMock()\n"
        )
        violations = check_source(source, "tests/unit/test_example.py")
        mock_violations = [v for v in violations if v[1] == "mock-spec-bypass"]
        assert len(mock_violations) == 1

    def test_allows_mock_without_spec(self) -> None:
        source = (
            "from unittest.mock import Mock, AsyncMock\n"
            "mock_obj = Mock()\n"
            "mock_obj.method = AsyncMock()\n"
        )
        violations = check_source(source, "tests/unit/test_example.py")
        mock_violations = [v for v in violations if v[1] == "mock-spec-bypass"]
        assert len(mock_violations) == 0

    def test_noqa_suppresses_mock_spec_bypass(self) -> None:
        source = (
            "from unittest.mock import Mock, AsyncMock\n"
            "mock_obj = Mock(spec=SomeClass)\n"
            "mock_obj.method = AsyncMock()  # noqa: mock-spec-bypass\n"
        )
        violations = check_source(source, "tests/unit/test_example.py")
        mock_violations = [v for v in violations if v[1] == "mock-spec-bypass"]
        assert len(mock_violations) == 0

    def test_only_applies_to_test_files(self) -> None:
        source = (
            "from unittest.mock import Mock, AsyncMock\n"
            "mock_obj = Mock(spec=SomeClass)\n"
            "mock_obj.method = AsyncMock()\n"
        )
        violations = check_source(source, "src/utils/helper.py")
        mock_violations = [v for v in violations if v[1] == "mock-spec-bypass"]
        assert len(mock_violations) == 0
