"""Tests for the em dash checker script."""

from pathlib import Path

from scripts.check_emdashes import check_file, check_file_content


def test_detects_emdash_in_content() -> None:
    """Content with an em dash returns a violation with correct line number."""
    content = "line one\nsome text \u2014 more text\nline three\n"
    violations = check_file_content(content)
    assert len(violations) == 1
    assert violations[0][0] == 2
    assert "\u2014" in violations[0][1] or "em dash" in violations[0][1].lower()


def test_no_violations_for_clean_content() -> None:
    """Content without em dashes returns empty list."""
    content = "line one\nsome text -- more text\nline three\n"
    violations = check_file_content(content)
    assert violations == []


def test_whitelisted_file_skipped(tmp_path: Path) -> None:
    """A whitelisted file produces no violations even if it contains em dashes."""
    f = tmp_path / "example.py"
    f.write_text("text \u2014 more text\n")

    violations = check_file(str(f), whitelist=[str(f)])
    assert violations == []


def test_binary_file_skipped(tmp_path: Path) -> None:
    """Binary file produces no violations."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\xff\xfe" * 100)

    violations = check_file(str(f), whitelist=[])
    assert violations == []


def test_multiple_emdashes_on_same_line() -> None:
    """A line with multiple em dashes produces one violation per line."""
    content = "first \u2014 second \u2014 third\n"
    violations = check_file_content(content)
    assert len(violations) == 1
    assert violations[0][0] == 1
