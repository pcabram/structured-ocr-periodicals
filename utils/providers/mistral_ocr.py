"""
Mistral OCR provider implementation.
Provides document extraction using Mistral's OCR API with PDF input.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from pydantic import BaseModel
from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model

from ._shared import encode_file_to_data_url

logger = logging.getLogger(__name__)


class MistralOCRProvider:
    """
    Provider for Mistral OCR API (mistral-ocr-latest).
    Uses client.ocr.process() with PDF document input.
    Optimized for document extraction with native PDF support.
    """

    def __init__(self, api_key: str, model_name: str = "mistral-ocr-latest"):
        """
        Initialize Mistral OCR provider.
        Args:
            api_key: Mistral API key
            model_name: Model identifier (default: "mistral-ocr-latest")
        """
        self.client = Mistral(api_key=api_key)
        self.model_name = model_name
        self._pdf_cache: dict[Path, str] = {}

    def process_page(
        self,
        pdf_path: Path,
        page_num: int,  # 1-indexed
        schema_class: type[BaseModel],
        **kwargs
    ) -> dict:
        """
        Extract data from PDF page using Mistral OCR.
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            schema_class: Pydantic schema for extraction
            **kwargs: Additional options (unused for OCR)
        Returns:
            Extracted data dict with at least {"items": [...]}
        """
        # Cache encoded PDF (only encode once per document)
        if pdf_path not in self._pdf_cache:
            self._pdf_cache[pdf_path] = encode_file_to_data_url(pdf_path)

        data_url = self._pdf_cache[pdf_path]
        page_idx = page_num - 1  # Convert to 0-indexed

        # Generate response format from schema
        doc_annot_fmt = response_format_from_pydantic_model(schema_class)

        # Call OCR API
        resp = self.client.ocr.process(
            model=self.model_name,
            document={"type": "document_url", "document_url": data_url},
            pages=[page_idx],
            document_annotation_format=doc_annot_fmt,
            include_image_base64=False,
        )

        # Parse and return response
        return self._parse_response(resp)

    def _parse_response(self, resp) -> dict:
        """
        Parse Mistral OCR API response.
        Handles different response formats:
        - resp.document_annotation (string or dict)
        - resp.pages[0].document_annotation (fallback)
        Args:
            resp: Mistral OCR API response object
        Returns:
            Annotation dict (empty dict if parsing fails)
        """
        # Try top-level document_annotation first
        ann = getattr(resp, "document_annotation", None)

        if isinstance(ann, str):
            try:
                return json.loads(ann)
            except json.JSONDecodeError:
                pass
        elif isinstance(ann, dict):
            return ann or {}

        # Fall back to pages array
        pages = getattr(resp, "pages", None) or []
        if pages:
            page_ann = getattr(pages[0], "document_annotation", None)

            if isinstance(page_ann, str):
                try:
                    return json.loads(page_ann)
                except json.JSONDecodeError:
                    return {}
            elif isinstance(page_ann, dict):
                return page_ann or {}

        return {}