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
    discover_all_extractions
)

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
]