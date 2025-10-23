"""Test OCR evaluation metrics."""

from utils.ocr_metrics import character_error_rate, word_error_rate


def test_cer_identical_strings():
    """CER is 0 for identical strings."""
    text = "hello world"
    assert character_error_rate(text, text, "standard") == 0.0


def test_cer_completely_different():
    """CER is 1.0 for completely different strings of same length."""
    cer = character_error_rate("abcde", "fghij", "standard")
    assert cer == 1.0


def test_cer_one_char_error():
    """CER correctly calculates single character error."""
    gold = "hello"
    pred = "helo"
    cer = character_error_rate(gold, pred, "standard")
    assert cer == 0.2


def test_wer_identical_strings():
    """WER is 0 for identical strings."""
    text = "hello world"
    assert word_error_rate(text, text, "standard") == 0.0


def test_wer_one_word_different():
    """WER correctly calculates single word error."""
    gold = "hello world"
    pred = "hello earth"
    wer = word_error_rate(gold, pred, "standard")
    assert wer == 0.5


def test_cer_normalization_levels():
    """Different normalization levels produce different results."""
    gold = "Hello  world!"
    pred = "Hello world"

    cer_strict = character_error_rate(gold, pred, "strict")
    cer_standard = character_error_rate(gold, pred, "standard")
    cer_letters = character_error_rate(gold, pred, "letters_only")

    assert cer_standard < cer_strict
    assert cer_letters < cer_standard


def test_empty_strings():
    """Metrics handle empty strings correctly."""
    assert character_error_rate("", "", "standard") == 0.0
    assert character_error_rate("", "text", "standard") == 1.0
    assert word_error_rate("", "", "standard") == 0.0
