"""
Text Processing Utilities for OCR Evaluation

Provides standardized text normalization functions used across OCR evaluation notebooks.
These functions prepare text for comparison by applying different levels of normalization.

Used by:
- 01c_extraction_evaluation.ipynb
- 01d_comparative_evaluation.ipynb
"""

import unicodedata
import re
from typing import List


def normalize_text_strict(text: str) -> str:
    """
    Apply strict normalization: only Unicode NFC normalization.
    
    Preserves all whitespace (including newlines), punctuation, and capitalization.
    Use this when you need to preserve exact formatting and spacing.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Text with Unicode NFC normalization applied
    """
    return unicodedata.normalize('NFC', text)


def normalize_text_standard(text: str) -> str:
    """
    Apply standard normalization for fair OCR evaluation.
    
    This normalization level for OCR evaluation:
    - Removes formatting differences (newlines vs spaces)
    - Preserves actual content (punctuation, capitalization, diacritics)
    
    Transformations:
    - Unicode NFC normalization
    - All whitespace (spaces, tabs, newlines) → single space
    - Strip leading/trailing whitespace
    
    Args:
        text: Input text to normalize
        
    Returns:
        Text with whitespace normalized to single spaces
    """
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'\s+', ' ', text)  # All whitespace → single space
    text = text.strip()
    return text


def normalize_text_letters_only(text: str) -> str:
    """
    Apply aggressive normalization: letters and numbers only.
    
    Measures pure character recognition quality, ignoring all
    formatting, punctuation, and spacing differences. Most lenient metric.
    
    Transformations:
    - Unicode NFC normalization
    - Remove all whitespace
    - Remove all punctuation
    - Preserve capitalization and diacritics (letters only)
    
    Args:
        text: Input text to normalize
        
    Returns:
        text with only word characters (letters, numbers, underscores)
    """
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[^\w]', '', text)  # Remove all non-word characters
    return text


def token_sort_text(text: str) -> str:
    """
    Sort tokens (words) alphabetically for order-agnostic comparison.
    
    This removes the impact of reading order on text similarity, allowing
    for comparison of OCR output quality when document structure detection may have
    failed but individual words were recognized correctly.
    
    Args:
        text: Input text (should be normalized first)
        
    Returns:
        Space-separated string with tokens in alphabetical order
    """
    tokens = text.split()
    return ' '.join(sorted(tokens))


# Convenience function for common workflow
def normalize_and_sort(text: str, normalization: str = 'standard') -> str:
    """
    Apply normalization and token sorting in one step.
    
    Args:
        text: Input text
        normalization: One of 'strict', 'standard', 'letters_only'
        
    Returns:
        Normalized and sorted text
    """
    if normalization == 'strict':
        normalized = normalize_text_strict(text)
    elif normalization == 'standard':
        normalized = normalize_text_standard(text)
    elif normalization == 'letters_only':
        normalized = normalize_text_letters_only(text)
    else:
        raise ValueError(f"Unknown normalization: {normalization}. Use 'strict', 'standard', or 'letters_only'.")
    
    return token_sort_text(normalized)