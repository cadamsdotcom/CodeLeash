"""Tests for check_frontend_code_quality.py - frontend code quality checks."""

from scripts.check_frontend_code_quality import check_source


class TestDialogDescriptionNesting:
    """Detect <p> elements nested inside Radix Dialog/AlertDialog Description."""

    def test_flags_p_inside_alert_dialog_description(self) -> None:
        source = (
            '<AlertDialog.Description className="mt-3 text-sm">\n'
            "  <p>Are you sure?</p>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 1
        assert nesting_violations[0][0] == 2  # line number of <p>

    def test_flags_p_inside_dialog_description(self) -> None:
        source = (
            '<Dialog.Description className="mt-3 text-sm">\n'
            "  <p>Some content</p>\n"
            "</Dialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 1

    def test_flags_multiple_p_tags(self) -> None:
        source = (
            '<AlertDialog.Description className="mt-3">\n'
            "  <p>First paragraph</p>\n"
            "  <p>Second paragraph</p>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 2

    def test_allows_as_child_with_div_wrapper(self) -> None:
        source = (
            "<AlertDialog.Description asChild>\n"
            '  <div className="mt-3 text-sm">\n'
            "    <p>This is fine because asChild renders as div</p>\n"
            "  </div>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 0

    def test_allows_text_only_content(self) -> None:
        source = (
            '<AlertDialog.Description className="mt-3 text-sm">\n'
            "  This document will be removed from the upload list.\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 0

    def test_allows_span_block_instead_of_p(self) -> None:
        source = (
            '<AlertDialog.Description className="mt-3 text-sm">\n'
            '  <span className="block mb-2">\n'
            "    Are you sure you want to delete this?\n"
            "  </span>\n"
            '  <span className="block">\n'
            "    This action cannot be undone.\n"
            "  </span>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 0

    def test_handles_as_child_on_separate_line(self) -> None:
        source = (
            "<AlertDialog.Description\n"
            "  asChild\n"
            '  className="mt-3"\n'
            ">\n"
            '  <div className="space-y-2">\n'
            "    <p>Safe because asChild is present</p>\n"
            "  </div>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 0

    def test_flags_p_with_multi_line_opening_tag_without_as_child(self) -> None:
        source = (
            "<AlertDialog.Description\n"
            '  className="mt-3 text-sm text-brand-mid-grey"\n'
            ">\n"
            "  <p>This is a violation</p>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 1
        assert nesting_violations[0][0] == 4

    def test_handles_self_closing_description(self) -> None:
        source = '<AlertDialog.Description className="sr-only" />\n'
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 0

    def test_handles_multiple_descriptions_in_one_file(self) -> None:
        source = (
            "// First dialog - safe (text only)\n"
            '<AlertDialog.Description className="mt-2">\n'
            "  Are you sure?\n"
            "</AlertDialog.Description>\n"
            "\n"
            "// Second dialog - violation\n"
            '<AlertDialog.Description className="mt-2">\n'
            "  <p>Bad nesting</p>\n"
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 1
        assert nesting_violations[0][0] == 8

    def test_p_with_attributes_is_also_flagged(self) -> None:
        source = (
            '<AlertDialog.Description className="mt-3">\n'
            '  <p className="text-sm">Content</p>\n'
            "</AlertDialog.Description>\n"
        )
        violations = check_source(source, "src/components/Example.tsx")
        nesting_violations = [v for v in violations if v[1] == "dialog-p-nesting"]
        assert len(nesting_violations) == 1
