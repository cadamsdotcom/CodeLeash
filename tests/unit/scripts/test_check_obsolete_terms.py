"""Tests for the obsolete terms checker script."""

import re
from pathlib import Path

from scripts.check_obsolete_terms import (
    ObsoleteTerm,
    check_file,
    check_file_content,
    check_filename,
    is_whitelisted,
)

_DODO = ObsoleteTerm(
    term="dodo",
    pattern=re.compile(r"dodo", re.IGNORECASE),
    replacement="greeting",
)


def test_is_whitelisted_exact_match() -> None:
    """File that appears in the whitelist should be whitelisted."""
    whitelist = ["app/foo.py", "app/bar.py"]
    assert is_whitelisted("app/foo.py", whitelist) is True


def test_is_whitelisted_no_match() -> None:
    """File not in the whitelist should not be whitelisted."""
    whitelist = ["app/foo.py", "app/bar.py"]
    assert is_whitelisted("app/baz.py", whitelist) is False


def test_detects_obsolete_term_in_content() -> None:
    """Should detect obsolete term in file content and return line number."""
    content = "line one\nthe dodo model\nline three\n"
    violations = check_file_content(content, _DODO)
    assert len(violations) == 1
    assert violations[0][0] == 2  # line number
    assert "dodo" in violations[0][1].lower()


def test_case_insensitive_detection() -> None:
    """Should detect the term regardless of case."""
    content = "The Dodo class is here\n"
    violations = check_file_content(content, _DODO)
    assert len(violations) == 1


def test_detects_obsolete_term_in_filename() -> None:
    """Should detect obsolete term in a filename."""
    result = check_filename("app/dodo_service.py", _DODO)
    assert result is not None
    assert "dodo" in result.lower()


def test_no_detection_in_clean_filename() -> None:
    """Should return None for a filename without the obsolete term."""
    result = check_filename("app/greeting_service.py", _DODO)
    assert result is None


def test_whitelisted_file_skipped(tmp_path: Path) -> None:
    """A whitelisted file should produce no violations even if it contains the term."""
    f = tmp_path / "check_script.py"
    f.write_text("term='dodo'\n")

    term = ObsoleteTerm(
        term="dodo",
        pattern=re.compile(r"dodo", re.IGNORECASE),
        replacement="greeting",
        whitelist=[str(f)],
    )
    violations = check_file(str(f), term)
    assert violations == []


def test_binary_file_skipped(tmp_path: Path) -> None:
    """Binary files should be skipped without error."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\xff\xfe" * 100)

    violations = check_file(str(f), _DODO)
    assert violations == []
