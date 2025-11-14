"""
Utility modules for Stage 1 OCR processing.
"""
from .extraction import (
    count_pages,
    encode_file_to_data_url,
    parse_annotation_response,
    call_with_retry,
    validate_extraction,
    extract_pdf_pages,
    extract_all_pdfs
)

from .paths import (
    build_evaluation_path,
    discover_all_extractions,
    discover_available_magazines,
    discover_existing_extractions,
    generate_all_combinations,
    calculate_missing_extractions,
    detect_schema_family
)

from .evaluation import (
    load_and_match_page,
    evaluate_order_agnostic,
    evaluate_structure_aware,
    evaluate_classification,
    evaluate_classification_detailed,
    evaluate_metadata_field,
    evaluate_continuation_all_items,
    calculate_word_coverage,
    calculate_character_coverage)

__all__ = [
    # Extraction
    'count_pages',
    'encode_file_to_data_url',
    'parse_annotation_response',
    'call_with_retry',
    'validate_extraction',
    'extract_pdf_pages',
    'extract_all_pdfs',
    # Evaluation paths
    'build_evaluation_path',
    'discover_all_extractions'
    'discover_available_magazines',
    'discover_existing_extractions',
    'generate_all_combinations',
    'calculate_missing_extractions',
    'detect_schema_family',
    # Evaluation metrics
    'load_and_match_page',
    'evaluate_order_agnostic',
    'evaluate_structure_aware',
    'evaluate_classification',
    'evaluate_classification_detailed',
    'evaluate_metadata_field',
    'evaluate_continuation_all_items',
    'calculate_word_coverage',
    'calculate_character_coverage'
]