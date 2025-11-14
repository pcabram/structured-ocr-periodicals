"""
Evaluation utilities for Stage 1 OCR
Shared functions for matching items and calculating evaluation metrics across all dimensions.

Used by:
- 01c_extraction_evaluation.ipynb (single schema evaluation)
- 01e_multi_schema_evaluation.ipynb (multi-schema comparison)

Evaluation dimensions:
1. Structure detection (item matching)
2. Text quality (CER/WER on matched content)
3. Classification (item_class accuracy)
4. Metadata extraction (title/author)
5. Continuation tracking (is_continuation, continues_on_next_page)
"""

from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
from difflib import SequenceMatcher
import re
import json

from schemas.stage1_page import Stage1PageModel
from .config import EVALUATION_CONFIG
from .text_processing import token_sort_text
from .ocr_metrics import character_error_rate, word_error_rate


# ============================================================================
# ITEM MATCHING
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for item matching (different from text_processing functions).
    Used specifically for comparing item_text_raw fields to find matches.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text (lowercase, no punctuation, single spaces)
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity ratio between two texts using SequenceMatcher.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Float between 0.0 (completely different) and 1.0 (identical)
    """
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    
    return SequenceMatcher(None, t1, t2).ratio()


def match_items(
    gold_items: List[Dict], 
    pred_items: List[Dict],
    similarity_threshold: float = EVALUATION_CONFIG.similarity_threshold
) -> Tuple[List[Tuple[int, int, float]], Set[int], Set[int]]:
    """
    Match gold items to prediction items using greedy best-match algorithm.
    
    Algorithm:
        For each gold item, find the best-matching unmatched pred item.
        Accept the match if similarity exceeds threshold.
    
    Args:
        gold_items: List of gold standard items
        pred_items: List of predicted items
        similarity_threshold: Minimum similarity score to consider a match
    
    Returns:
        Tuple of:
        - matches: List of (gold_idx, pred_idx, similarity_score)
        - unmatched_gold: Set of gold indices with no match
        - unmatched_pred: Set of pred indices with no match
    """
    matches = []
    matched_pred_indices = set()
    unmatched_gold = set()
    
    for gold_idx, gold_item in enumerate(gold_items):
        gold_text = gold_item.get('item_text_raw', '')
        
        best_score = 0.0
        best_pred_idx = None
        
        for pred_idx, pred_item in enumerate(pred_items):
            if pred_idx in matched_pred_indices:
                continue
            
            pred_text = pred_item.get('item_text_raw', '')
            score = text_similarity(gold_text, pred_text)
            
            if score > best_score:
                best_score = score
                best_pred_idx = pred_idx
        
        if best_score >= similarity_threshold and best_pred_idx is not None:
            matches.append((gold_idx, best_pred_idx, best_score))
            matched_pred_indices.add(best_pred_idx)
        else:
            unmatched_gold.add(gold_idx)
    
    unmatched_pred = set(range(len(pred_items))) - matched_pred_indices
    
    return matches, unmatched_gold, unmatched_pred


def load_and_match_page(
    gold_path: Path, 
    pred_path: Path,
    similarity_threshold: float = EVALUATION_CONFIG.similarity_threshold
) -> Dict:
    """
    Load a page pair and match items.
    
    Args:
        gold_path: Path to gold standard JSON
        pred_path: Path to prediction JSON
        similarity_threshold: Minimum similarity for matching
    
    Returns:
        Dict with:
        - gold_items: All gold items
        - pred_items: All pred items
        - matches: List of (gold_idx, pred_idx, score) tuples
        - unmatched_gold: Set of unmatched gold indices
        - unmatched_pred: Set of unmatched pred indices
        - page_name: Filename
    """
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    gold_page = Stage1PageModel.model_validate(gold_data)
    gold_data = gold_page.model_dump()
    
    with open(pred_path, 'r', encoding='utf-8') as f:
        pred_data = json.load(f)
    pred_page = Stage1PageModel.model_validate(pred_data)
    pred_data = pred_page.model_dump()
    
    gold_items = gold_data.get('items', [])
    pred_items = pred_data.get('items', [])
    
    matches, unmatched_gold, unmatched_pred = match_items(
        gold_items, pred_items, similarity_threshold
    )
    
    return {
        'gold_items': gold_items,
        'pred_items': pred_items,
        'matches': matches,
        'unmatched_gold': unmatched_gold,
        'unmatched_pred': unmatched_pred,
        'page_name': gold_path.name
    }


def filter_matches_by_class(
    matches: List[Tuple[int, int, float]],
    gold_items: List[Dict],
    item_classes: List[str]
) -> List[Tuple[int, int, float]]:
    """
    Filter matches to only include items of specified classes.
    
    Args:
        matches: List of (gold_idx, pred_idx, score) tuples
        gold_items: List of gold standard items
        item_classes: List of classes to include (e.g., ['prose', 'verse'])
    
    Returns:
        Filtered list of matches
    """
    return [
        (g_idx, p_idx, score) 
        for g_idx, p_idx, score in matches
        if gold_items[g_idx]['item_class'] in item_classes
    ]


def get_matched_pairs(
    matches: List[Tuple[int, int, float]],
    gold_items: List[Dict],
    pred_items: List[Dict]
) -> List[Tuple[Dict, Dict, float]]:
    """
    Convert match indices to actual item pairs.
    
    Args:
        matches: List of (gold_idx, pred_idx, score) tuples
        gold_items: List of gold standard items
        pred_items: List of predicted items
    
    Returns:
        List of (gold_item, pred_item, similarity_score) tuples
    """
    return [
        (gold_items[g_idx], pred_items[p_idx], score)
        for g_idx, p_idx, score in matches
    ]


# ============================================================================
# TEXT QUALITY EVALUATION
# ============================================================================

def evaluate_order_agnostic(
    gold_items: List[Dict], 
    pred_items: List[Dict], 
    item_classes: Optional[List[str]] = None
) -> Dict:
    """
    Evaluate text quality without considering reading order.
    Uses token sort ratio approach - sorts all words before comparison.
    
    Args:
        gold_items: List of gold standard items
        pred_items: List of predicted items
        item_classes: If provided, filter to only these classes
    
    Returns:
        Dict with CER, WER for standard and letters_only normalization
    """
    if item_classes:
        gold_items = [item for item in gold_items if item['item_class'] in item_classes]
        pred_items = [item for item in pred_items if item['item_class'] in item_classes]
    
    gold_text = ' '.join(item.get('item_text_raw', '') for item in gold_items)
    pred_text = ' '.join(item.get('item_text_raw', '') for item in pred_items)
    
    gold_sorted = token_sort_text(gold_text)
    pred_sorted = token_sort_text(pred_text)
    
    results = {
        'cer_standard': character_error_rate(gold_sorted, pred_sorted, 'standard'),
        'wer_standard': word_error_rate(gold_sorted, pred_sorted, 'standard'),
        'cer_letters': character_error_rate(gold_sorted, pred_sorted, 'letters_only'),
        'gold_chars': len(gold_text),
        'pred_chars': len(pred_text),
        'gold_words': len(gold_text.split()),
        'pred_words': len(pred_text.split())
    }
    
    return results


def evaluate_structure_aware(
    gold_items: List[Dict], 
    pred_items: List[Dict],
    matches: List[Tuple[int, int, float]],
    item_classes: Optional[List[str]] = None
) -> Dict:
    """
    Evaluate text quality on matched pairs, respecting document structure.
    Only compares content that was successfully aligned via matching.
    
    Args:
        gold_items: List of gold standard items
        pred_items: List of predicted items
        matches: List of (gold_idx, pred_idx, score) tuples
        item_classes: If provided, filter matches to only these classes
    
    Returns:
        Dict with matched CER/WER and unmatched content statistics
    """
    if item_classes:
        filtered_matches = filter_matches_by_class(matches, gold_items, item_classes)
    else:
        filtered_matches = matches
    
    matched_pairs = get_matched_pairs(filtered_matches, gold_items, pred_items)
    
    if matched_pairs:
        gold_matched_text = ' '.join(gold_item.get('item_text_raw', '') 
                                     for gold_item, _, _ in matched_pairs)
        pred_matched_text = ' '.join(pred_item.get('item_text_raw', '') 
                                     for _, pred_item, _ in matched_pairs)
        
        cer_standard = character_error_rate(gold_matched_text, pred_matched_text, 'standard')
        wer_standard = word_error_rate(gold_matched_text, pred_matched_text, 'standard')
        cer_letters = character_error_rate(gold_matched_text, pred_matched_text, 'letters_only')
        
        matched_gold_chars = len(gold_matched_text)
        matched_pred_chars = len(pred_matched_text)
    else:
        cer_standard = 0.0
        wer_standard = 0.0
        cer_letters = 0.0
        matched_gold_chars = 0
        matched_pred_chars = 0
    
    matched_gold_indices = {g_idx for g_idx, _, _ in filtered_matches}
    matched_pred_indices = {p_idx for _, p_idx, _ in filtered_matches}
    
    if item_classes:
        unmatched_gold_items = [
            gold_items[i] for i in range(len(gold_items))
            if i not in matched_gold_indices and gold_items[i]['item_class'] in item_classes
        ]
        unmatched_pred_items = [
            pred_items[i] for i in range(len(pred_items))
            if i not in matched_pred_indices and pred_items[i]['item_class'] in item_classes
        ]
        total_gold_chars = sum(len(item.get('item_text_raw', '')) 
                              for item in gold_items if item['item_class'] in item_classes)
    else:
        unmatched_gold_items = [gold_items[i] for i in range(len(gold_items)) 
                               if i not in matched_gold_indices]
        unmatched_pred_items = [pred_items[i] for i in range(len(pred_items)) 
                               if i not in matched_pred_indices]
        total_gold_chars = sum(len(item.get('item_text_raw', '')) for item in gold_items)
    
    unmatched_gold_chars = sum(len(item.get('item_text_raw', '')) 
                               for item in unmatched_gold_items)
    unmatched_pred_chars = sum(len(item.get('item_text_raw', '')) 
                               for item in unmatched_pred_items)
    
    return {
        'cer_standard': cer_standard,
        'wer_standard': wer_standard,
        'cer_letters': cer_letters,
        'matched_gold_chars': matched_gold_chars,
        'matched_pred_chars': matched_pred_chars,
        'unmatched_gold_chars': unmatched_gold_chars,
        'unmatched_pred_chars': unmatched_pred_chars,
        'total_gold_chars': total_gold_chars,
        'matched_percentage': (matched_gold_chars / total_gold_chars * 100) if total_gold_chars else 0
    }


# ============================================================================
# CLASSIFICATION EVALUATION
# ============================================================================

def evaluate_classification(
    gold_items: List[Dict], 
    pred_items: List[Dict],
    matches: List[Tuple[int, int, float]]
) -> Dict:
    """
    Evaluate classification accuracy on matched pairs.
    
    Args:
        gold_items: List of gold standard items
        pred_items: List of predicted items
        matches: List of (gold_idx, pred_idx, score) tuples
    
    Returns:
        Dict with gold_classes, pred_classes, correct count, total, and accuracy
    """
    if not matches:
        return {
            'gold_classes': [],
            'pred_classes': [],
            'correct': 0,
            'total': 0,
            'accuracy': 0.0
        }
    
    matched_pairs = get_matched_pairs(matches, gold_items, pred_items)
    
    gold_classes = []
    pred_classes = []
    
    for gold_item, pred_item, _ in matched_pairs:
        gold_classes.append(gold_item['item_class'])
        pred_classes.append(pred_item['item_class'])
    
    correct = sum(1 for g, p in zip(gold_classes, pred_classes) if g == p)
    total = len(gold_classes)
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        'gold_classes': gold_classes,
        'pred_classes': pred_classes,
        'correct': correct,
        'total': total,
        'accuracy': accuracy
    }


# ============================================================================
# METADATA EVALUATION
# ============================================================================

def normalize_metadata_string(s: Optional[str]) -> str:
    """
    Normalize metadata string for comparison.
    
    Args:
        s: Metadata string (title or author)
        
    Returns:
        Normalized string
    """
    if s is None:
        return ""
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)
    s = s.strip('.,;:!?')
    return s


def metadata_similarity(gold: Optional[str], pred: Optional[str]) -> float:
    """
    Calculate similarity between two metadata strings.
    
    Args:
        gold: Gold standard metadata
        pred: Predicted metadata
        
    Returns:
        Float between 0.0 and 1.0
    """
    gold_norm = normalize_metadata_string(gold)
    pred_norm = normalize_metadata_string(pred)
    
    if not gold_norm and not pred_norm:
        return 1.0
    if not gold_norm or not pred_norm:
        return 0.0
    
    if gold_norm == pred_norm:
        return 1.0
    
    return SequenceMatcher(None, gold_norm, pred_norm).ratio()


def evaluate_metadata_field(
    gold_items: List[Dict], 
    pred_items: List[Dict],
    matches: List[Tuple[int, int, float]],
    field_name: str,
    similarity_threshold: float = 0.8
) -> Dict:
    """
    Evaluate a specific metadata field (title or author).
    
    Args:
        gold_items: List of gold items
        pred_items: List of pred items
        matches: List of (gold_idx, pred_idx, score) tuples
        field_name: 'item_title' or 'item_author'
        similarity_threshold: Minimum similarity for partial match
    
    Returns:
        Dict with precision, recall, F1, and match counts
    """
    if not matches:
        return {
            'gold_present': 0,
            'pred_present': 0,
            'exact_matches': 0,
            'partial_matches': 0,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0
        }
    
    matched_pairs = get_matched_pairs(matches, gold_items, pred_items)
    
    gold_present = 0
    pred_present = 0
    exact_matches = 0
    partial_matches = 0
    
    for gold_item, pred_item, _ in matched_pairs:
        gold_value = gold_item.get(field_name)
        pred_value = pred_item.get(field_name)
        
        gold_has_value = gold_value is not None and gold_value.strip() != ''
        pred_has_value = pred_value is not None and pred_value.strip() != ''
        
        if gold_has_value:
            gold_present += 1
        
        if pred_has_value:
            pred_present += 1
        
        if gold_has_value and pred_has_value:
            similarity = metadata_similarity(gold_value, pred_value)
            
            if similarity == 1.0:
                exact_matches += 1
                partial_matches += 1
            elif similarity >= similarity_threshold:
                partial_matches += 1
    
    precision = partial_matches / pred_present if pred_present > 0 else 0.0
    recall = partial_matches / gold_present if gold_present > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'gold_present': gold_present,
        'pred_present': pred_present,
        'exact_matches': exact_matches,
        'partial_matches': partial_matches,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


# ============================================================================
# CONTINUATION EVALUATION
# ============================================================================

def evaluate_continuation_all_items(
    gold_items: List[Dict],
    pred_items: List[Dict],
    matches: List[Tuple[int, int, float]],
    unmatched_gold: Set[int],
    unmatched_pred: Set[int]
) -> Dict:
    """
    Evaluate continuation field accuracy across ALL items.
    
    Args:
        gold_items: Gold standard items
        pred_items: Predicted items
        matches: List of (gold_idx, pred_idx, similarity) tuples
        unmatched_gold: Set of unmatched gold indices
        unmatched_pred: Set of unmatched pred indices
        
    Returns:
        Dict with metrics for is_continuation and continues_on_next_page
    """
    is_cont_tp = is_cont_fp = is_cont_fn = is_cont_tn = 0
    continues_tp = continues_fp = continues_fn = continues_tn = 0
    
    # 1. Evaluate matched items
    for gold_idx, pred_idx, _ in matches:
        gold_item = gold_items[gold_idx]
        pred_item = pred_items[pred_idx]
        
        # Evaluate is_continuation
        gold_is_cont = gold_item.get('is_continuation') is True
        pred_is_cont = pred_item.get('is_continuation') is True
        
        if gold_is_cont and pred_is_cont:
            is_cont_tp += 1
        elif not gold_is_cont and pred_is_cont:
            is_cont_fp += 1
        elif gold_is_cont and not pred_is_cont:
            is_cont_fn += 1
        else:
            is_cont_tn += 1
        
        # Evaluate continues_on_next_page
        gold_continues = gold_item.get('continues_on_next_page') is True
        pred_continues = pred_item.get('continues_on_next_page') is True
        
        if gold_continues and pred_continues:
            continues_tp += 1
        elif not gold_continues and pred_continues:
            continues_fp += 1
        elif gold_continues and not pred_continues:
            continues_fn += 1
        else:
            continues_tn += 1
    
    # 2. Evaluate unmatched gold items (missed continuations = FN)
    for gold_idx in unmatched_gold:
        gold_item = gold_items[gold_idx]
        
        if gold_item.get('is_continuation') is True:
            is_cont_fn += 1
        
        if gold_item.get('continues_on_next_page') is True:
            continues_fn += 1
    
    # 3. Evaluate unmatched pred items (hallucinated continuations = FP)
    for pred_idx in unmatched_pred:
        pred_item = pred_items[pred_idx]
        
        if pred_item.get('is_continuation') is True:
            is_cont_fp += 1
        
        if pred_item.get('continues_on_next_page') is True:
            continues_fp += 1
    
    # Calculate metrics for is_continuation
    is_cont_p = is_cont_tp / (is_cont_tp + is_cont_fp) if (is_cont_tp + is_cont_fp) > 0 else 0.0
    is_cont_r = is_cont_tp / (is_cont_tp + is_cont_fn) if (is_cont_tp + is_cont_fn) > 0 else 0.0
    is_cont_f1 = 2 * is_cont_p * is_cont_r / (is_cont_p + is_cont_r) if (is_cont_p + is_cont_r) > 0 else 0.0
    
    # Calculate metrics for continues_on_next_page
    continues_p = continues_tp / (continues_tp + continues_fp) if (continues_tp + continues_fp) > 0 else 0.0
    continues_r = continues_tp / (continues_tp + continues_fn) if (continues_tp + continues_fn) > 0 else 0.0
    continues_f1 = 2 * continues_p * continues_r / (continues_p + continues_r) if (continues_p + continues_r) > 0 else 0.0
    
    return {
        'is_continuation': {
            'tp': is_cont_tp,
            'fp': is_cont_fp,
            'fn': is_cont_fn,
            'tn': is_cont_tn,
            'precision': is_cont_p,
            'recall': is_cont_r,
            'f1': is_cont_f1
        },
        'continues_on_next_page': {
            'tp': continues_tp,
            'fp': continues_fp,
            'fn': continues_fn,
            'tn': continues_tn,
            'precision': continues_p,
            'recall': continues_r,
            'f1': continues_f1
        }
    }

# ============================================================================
# WORD AND CHARACTER COVERAGE (FROM 01d)
# ============================================================================

def calculate_word_coverage(reference: str, hypothesis: str, normalization: str = 'standard') -> Dict:
    """
    Calculate word-level precision, recall, and F1 (bag-of-words).

    Order-agnostic comparison using set operations.

    Args:
        reference: Reference text (gold standard)
        hypothesis: Hypothesis text (OCR output)
        normalization: Normalization level ('strict', 'standard', 'letters_only')

    Returns:
        Dict with precision, recall, f1, and word counts
    """
    from .text_processing import normalize_text_strict, normalize_text_standard

    # Apply normalization
    if normalization == 'strict':
        ref = normalize_text_strict(reference)
        hyp = normalize_text_strict(hypothesis)
    elif normalization == 'standard':
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    elif normalization == 'letters_only':
        # Use standard for word-level (need word boundaries)
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    else:
        ref = reference
        hyp = hypothesis

    words_ref = set(ref.split())
    words_hyp = set(hyp.split())

    if len(words_ref) == 0 and len(words_hyp) == 0:
        precision = 1.0
        recall = 1.0
    elif len(words_hyp) == 0:
        precision = 0.0
        recall = 0.0
    elif len(words_ref) == 0:
        precision = 0.0
        recall = 0.0
    else:
        # Precision: % of hypothesis words that appear in reference
        precision = len(words_ref & words_hyp) / len(words_hyp)
        recall = len(words_ref & words_hyp) / len(words_ref)

    # Calculate F1
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'shared_words': len(words_ref & words_hyp),
        'unique_to_hyp': len(words_hyp - words_ref),
        'unique_to_ref': len(words_ref - words_hyp),
        'total_ref_words': len(words_ref),
        'total_hyp_words': len(words_hyp)
    }


def calculate_character_coverage(reference: str, hypothesis: str, normalization: str = 'letters_only') -> Dict:
    """
    Calculate character-level precision, recall, and F1 (bag-of-chars with frequency).

    Uses Counter to respect character frequency. Order-agnostic.
    Best used with 'letters_only' normalization.

    Args:
        reference: Reference text (gold standard)
        hypothesis: Hypothesis text (OCR output)
        normalization: Normalization level ('letters_only', 'standard', 'strict')

    Returns:
        Dict with precision, recall, f1, and character counts
    """
    from collections import Counter
    from .text_processing import normalize_text_strict, normalize_text_standard, normalize_text_letters_only

    # Apply normalization
    if normalization == 'letters_only':
        ref = normalize_text_letters_only(reference)
        hyp = normalize_text_letters_only(hypothesis)
    elif normalization == 'standard':
        ref = normalize_text_standard(reference)
        hyp = normalize_text_standard(hypothesis)
    else:  # strict
        ref = normalize_text_strict(reference)
        hyp = normalize_text_strict(hypothesis)

    # Count character frequencies
    ref_counter = Counter(ref)
    hyp_counter = Counter(hyp)

    # Calculate matches (minimum count for each character)
    matches = ref_counter & hyp_counter
    matched_count = sum(matches.values())

    total_ref = sum(ref_counter.values())
    total_hyp = sum(hyp_counter.values())

    # Calculate metrics
    if total_ref == 0 and total_hyp == 0:
        precision = 1.0
        recall = 1.0
        f1 = 1.0
    elif total_hyp == 0:
        precision = 0.0
        recall = 0.0
        f1 = 0.0
    elif total_ref == 0:
        precision = 0.0
        recall = 0.0
        f1 = 0.0
    else:
        precision = matched_count / total_hyp
        recall = matched_count / total_ref
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Diagnostic metrics
    unique_ref_chars = len(ref_counter)
    unique_hyp_chars = len(hyp_counter)
    unique_matched_chars = len(matches)

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'matched_chars': matched_count,
        'total_ref_chars': total_ref,
        'total_hyp_chars': total_hyp,
        'unique_ref_chars': unique_ref_chars,
        'unique_hyp_chars': unique_hyp_chars,
        'unique_matched_chars': unique_matched_chars
    }


# ============================================================================
# DETAILED CLASSIFICATION METRICS (FROM 01c)
# ============================================================================

def evaluate_classification_detailed(
    gold_items: List[Dict],
    pred_items: List[Dict],
    matches: List[Tuple[int, int, float]],
    class_labels: Optional[List[str]] = None
) -> Dict:
    """
    Evaluate classification with per-class metrics and confusion matrix.

    Args:
        gold_items: List of gold standard items
        pred_items: List of predicted items
        matches: List of (gold_idx, pred_idx, score) tuples
        class_labels: List of class labels (default: ['prose', 'verse', 'ad', 'paratext', 'unknown'])

    Returns:
        Dict with overall accuracy, per-class metrics, confusion matrix, and macro/weighted averages
    """
    import numpy as np

    if class_labels is None:
        class_labels = ['prose', 'verse', 'ad', 'paratext', 'unknown']

    if not matches:
        return {
            'overall_accuracy': 0.0,
            'per_class': {},
            'confusion_matrix': np.zeros((len(class_labels), len(class_labels))),
            'macro_avg': {'precision': 0.0, 'recall': 0.0, 'f1': 0.0},
            'weighted_avg': {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        }

    matched_pairs = get_matched_pairs(matches, gold_items, pred_items)

    gold_classes = []
    pred_classes = []

    for gold_item, pred_item, _ in matched_pairs:
        gold_classes.append(gold_item['item_class'])
        pred_classes.append(pred_item['item_class'])

    # Overall accuracy
    correct = sum(1 for g, p in zip(gold_classes, pred_classes) if g == p)
    total = len(gold_classes)
    overall_accuracy = correct / total if total > 0 else 0.0

    # Confusion matrix
    cm = np.zeros((len(class_labels), len(class_labels)), dtype=int)

    label_to_idx = {label: idx for idx, label in enumerate(class_labels)}

    for g_class, p_class in zip(gold_classes, pred_classes):
        if g_class in label_to_idx and p_class in label_to_idx:
            g_idx = label_to_idx[g_class]
            p_idx = label_to_idx[p_class]
            cm[g_idx][p_idx] += 1

    # Per-class metrics
    per_class = {}
    precisions = []
    recalls = []
    f1s = []
    supports = []

    for i, label in enumerate(class_labels):
        tp = cm[i][i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support
        }

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        supports.append(support)

    # Macro average (unweighted)
    macro_precision = np.mean(precisions)
    macro_recall = np.mean(recalls)
    macro_f1 = np.mean(f1s)

    # Weighted average (by support)
    total_support = sum(supports)
    if total_support > 0:
        weighted_precision = sum(p * s for p, s in zip(precisions, supports)) / total_support
        weighted_recall = sum(r * s for r, s in zip(recalls, supports)) / total_support
        weighted_f1 = sum(f * s for f, s in zip(f1s, supports)) / total_support
    else:
        weighted_precision = 0.0
        weighted_recall = 0.0
        weighted_f1 = 0.0

    return {
        'overall_accuracy': overall_accuracy,
        'per_class': per_class,
        'confusion_matrix': cm,
        'class_labels': class_labels,
        'macro_avg': {
            'precision': macro_precision,
            'recall': macro_recall,
            'f1': macro_f1
        },
        'weighted_avg': {
            'precision': weighted_precision,
            'recall': weighted_recall,
            'f1': weighted_f1
        }
    }