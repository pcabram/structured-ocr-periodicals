"""
Base protocol for model providers.
Defines the interface that all document extraction providers must implement.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable
from pathlib import Path
from pydantic import BaseModel


@runtime_checkable
class ModelProvider(Protocol):
    """
    Protocol defining interface for document extraction providers.
    All providers must implement the process_page() method to extract
    structured data from PDF pages using their respective AI models.

    Attributes:
        model_name: Identifier for the model (e.g., "mistral-ocr-latest")
    """

    model_name: str

    def process_page(
        self,
        pdf_path: Path,
        page_num: int,  # 1-indexed
        schema_class: type[BaseModel],
        **kwargs
    ) -> dict:
        """
        Extract structured data from a single PDF page.

        Args:
            pdf_path: Path to the PDF file to process
            page_num: Page number to extract (1-indexed)
            schema_class: Pydantic model defining the extraction schema
            **kwargs: Provider-specific options (e.g., retry settings)

        Returns:
            Dictionary containing extracted data. Must include at least:
            - "items": List of extracted items matching schema_class.
        """
        ...