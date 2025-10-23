"""Test text normalization functions."""

from utils.text_processing import (normalize_text_letters_only,
                                   normalize_text_standard,
                                   normalize_text_strict, token_sort_text)


def test_normalize_strict_preserves_whitespace():
    """Strict normalization preserves all whitespace."""
    text = "Hello\n\nworld  test"
    result = normalize_text_strict(text)
    assert "\n\n" in result
    assert "  " in result


def test_normalize_standard_collapses_whitespace():
    """Standard normalization collapses whitespace to single spaces."""
    text = "Hello   \n\n  world\t\ttest"
    result = normalize_text_standard(text)
    assert result == "Hello world test"


def test_normalize_standard_strips_edges():
    """Standard normalization strips leading/trailing whitespace."""
    text = "  \n  Hello world  \n  "
    result = normalize_text_standard(text)
    assert result == "Hello world"


def test_normalize_letters_only_removes_punctuation():
    """Letters-only removes all non-word characters."""
    text = "Hello, world! Test."
    result = normalize_text_letters_only(text)
    assert "," not in result
    assert "!" not in result
    assert "." not in result


def test_normalize_letters_only_removes_spaces():
    """Letters-only removes all whitespace."""
    text = "Hello world test"
    result = normalize_text_letters_only(text)
    assert " " not in result


def test_token_sort_alphabetical():
    """Token sort orders words alphabetically."""
    text = "zebra apple banana"
    result = token_sort_text(text)
    assert result == "apple banana zebra"


def test_normalization_preserves_french_accents():
    """Normalization preserves French diacritics."""
    text = "café élève"
    assert "é" in normalize_text_strict(text)
    assert "é" in normalize_text_standard(text)
    assert "é" in normalize_text_letters_only(text)
