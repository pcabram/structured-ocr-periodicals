"""
OCR Evaluation Metrics

Provides standard OCR quality metrics (CER, WER) using Levenshtein distance.
These functions calculate error rates at character and word levels with
support for multiple normalization strategies.

Used by:
- 01c_extraction_evaluation.ipynb (internal Mistral quality evaluation)
- 01d_comparative_evaluation.ipynb (Mistral vs BnF comparison)
"""

import Levenshtein
from typing import Literal

# Import normalization functions from sibling module
from .text_processing import (
    normalize_text_strict,
    normalize_text_standard,
    normalize_text_letters_only
)


NormalizationType = Literal['strict', 'standard', 'letters_only']


def character_error_rate(
    reference: str, 
    hypothesis: str, 
    normalization: NormalizationType = 'strict'
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
        - Use 'standard' normalization for fair OCR comparison (recommended)
        - Use 'letters_only' to measure pure character recognition accuracy
        - Empty reference returns 1.0 if hypothesis non-empty, else 0.0
    """
    # Apply normalization
    if normalization == 'strict':
        ref = normalize_text_strict(reference)
        hyp = normalize_text_strict(hypothesis)
    elif normalization == 'standard':
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    elif normalization == 'letters_only':
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
    reference: str, 
    hypothesis: str, 
    normalization: NormalizationType = 'strict'
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
            - 'standard': Normalize whitespace (RECOMMENDED)
            - 'letters_only': Uses 'standard' instead (needs word boundaries)
    
    Returns:
        Float between 0.0 (perfect) and ∞. Typical values:
        - 0.00-0.05: Excellent OCR quality
        - 0.05-0.15: Good quality
        - 0.15-0.30: Acceptable (needs correction)
        - >0.30: Poor quality
    
    Examples:
        >>> word_error_rate("hello world", "helo world", 'standard')
        0.5  # 1 word error in 2 words = 50%
        
        >>> word_error_rate("the quick brown fox", "the quick fox", 'standard')
        0.25  # 1 deletion in 4 words = 25%
        
        >>> word_error_rate("hello world", "world hello", 'standard')
        1.0  # Both words substituted (order matters!)
    
    Note:
        - WER treats word order changes as errors (use token_sort_text for
          order-agnostic comparison)
        - 'letters_only' normalization doesn't make sense for WER, so it
          falls back to 'standard'
        - Empty reference returns 1.0 if hypothesis non-empty, else 0.0
    
    Reference:
        Originally from speech recognition, now standard in OCR evaluation.
        See: https://en.wikipedia.org/wiki/Word_error_rate
    """
    # Apply normalization
    if normalization == 'strict':
        ref = normalize_text_strict(reference)
        hyp = normalize_text_strict(hypothesis)
    elif normalization == 'standard':
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    elif normalization == 'letters_only':
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
    normalizations: list[NormalizationType] = ['strict', 'standard', 'letters_only']
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
    
    Examples:
        >>> results = evaluate_text_quality("hello world", "helo world")
        >>> results['standard']['cer']
        0.09090909090909091
    """
    results = {}
    
    for norm in normalizations:
        cer = character_error_rate(reference, hypothesis, norm)
        wer = word_error_rate(reference, hypothesis, norm)
        
        results[norm] = {
            'cer': cer,
            'wer': wer
        }
    
    return results