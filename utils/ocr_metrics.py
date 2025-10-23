"""
OCR Evaluation Metrics

Provides standard OCR quality metrics (CER, WER) using Levenshtein distance.
These functions calculate error rates at character and word levels with
support for multiple normalization strategies.

Used by:
- 01c_extraction_evaluation.ipynb (internal Mistral quality evaluation)
- 01d_comparative_evaluation.ipynb (Mistral vs BnF comparison)
"""

from typing import Literal

import Levenshtein

# Import normalization functions from sibling module
from .text_processing import (normalize_text_letters_only,
                              normalize_text_standard, normalize_text_strict)

NormalizationType = Literal["strict", "standard", "letters_only"]


def character_error_rate(
    reference: str, hypothesis: str, normalization: NormalizationType = "strict"
) -> float:
    """
    Calculate Character Error Rate (CER) using Levenshtein distance.

    Formula:
        CER = (insertions + deletions + substitutions) / len(reference)

    Args:
        reference: Ground truth text (gold standard)
        hypothesis: OCR output text to evaluate
        normalization: Text normalization level to apply before comparison
            - 'strict': Only Unicode NFC (preserves all whitespace/punctuation)
            - 'standard': Normalize whitespace to single spaces
            - 'letters_only': Remove all whitespace and punctuation

    Returns:
        Float between 0.0 and ∞.

    Note:
        - Use 'standard' normalization for fair OCR comparison
        - Use 'letters_only' to measure pure character recognition accuracy
        - Empty reference returns 1.0 if hypothesis non-empty, else 0.0
    """
    # Apply normalization
    if normalization == "strict":
        ref = normalize_text_strict(reference)
        hyp = normalize_text_strict(hypothesis)
    elif normalization == "standard":
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    elif normalization == "letters_only":
        ref = normalize_text_letters_only(reference)
        hyp = normalize_text_letters_only(hypothesis)
    else:
        raise ValueError(f"Unknown normalization: {normalization}")

    # Handle empty reference
    if not ref:
        return 1.0 if hyp else 0.0

    # Calculate Levenshtein distance and normalize
    distance = Levenshtein.distance(ref, hyp)
    return distance / len(ref)


def word_error_rate(
    reference: str, hypothesis: str, normalization: NormalizationType = "strict"
) -> float:
    """
    Calculate Word Error Rate (WER) using Levenshtein distance on word sequences.

    WER measures the minimum number of word-level edits (insertions,
    deletions, substitutions) needed to transform the hypothesis into the
    reference, normalized by reference word count.

    Formula:
        WER = (insertions + deletions + substitutions) / word_count(reference)

    Args:
        reference: Ground truth text (gold standard)
        hypothesis: OCR output text to evaluate
        normalization: Text normalization level to apply before comparison
            - 'strict': Only Unicode NFC
            - 'standard': Normalize whitespace
            - 'letters_only': Uses 'standard' instead (needs word boundaries)

    Returns:
        Float between 0.0 (perfect) and ∞.
    """
    # Apply normalization
    if normalization == "strict":
        ref = normalize_text_strict(reference)
        hyp = normalize_text_strict(hypothesis)
    elif normalization == "standard":
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    elif normalization == "letters_only":
        # WER doesn't make sense without word boundaries, use standard
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    else:
        raise ValueError(f"Unknown normalization: {normalization}")

    # Split into words
    ref_words = ref.split()
    hyp_words = hyp.split()

    # Handle empty reference
    if not ref_words:
        return 1.0 if hyp_words else 0.0

    # Calculate Levenshtein distance on word sequences
    distance = Levenshtein.distance(ref_words, hyp_words)
    return distance / len(ref_words)


# Convenience function for batch evaluation
def evaluate_text_quality(
    reference: str,
    hypothesis: str,
    normalizations: list[NormalizationType] = ["strict", "standard", "letters_only"],
) -> dict[str, dict[str, float]]:
    """
    Evaluate OCR quality at multiple normalization levels.

    Args:
        reference: Ground truth text
        hypothesis: OCR output text
        normalizations: List of normalization levels to evaluate

    Returns:
        Nested dict with structure:
        {
            'strict': {'cer': 0.05, 'wer': 0.10},
            'standard': {'cer': 0.03, 'wer': 0.08},
            'letters_only': {'cer': 0.02, 'wer': 0.0}
        }
    """
    results = {}

    for norm in normalizations:
        cer = character_error_rate(reference, hypothesis, norm)
        wer = word_error_rate(reference, hypothesis, norm)

        results[norm] = {"cer": cer, "wer": wer}

    return results
