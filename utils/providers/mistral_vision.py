"""
Mistral Vision provider implementation.
Provides document extraction using Mistral's vision models with image input
and structured output parsing.
Supports models: pixtral-12b-latest, pixtral-large-latest, mistral-medium-2508,
mistral-small-2506, and other vision-capable Mistral models.
"""
from __future__ import annotations

import logging
from pathlib import Path
from pydantic import BaseModel
from mistralai import Mistral

from ._shared import pdf_page_to_base64_image

logger = logging.getLogger(__name__)


class MistralVisionProvider:
    """
    Provider for Mistral vision models with structured output support.
    Uses client.chat.parse() with image input and Pydantic schema validation.
    Supports both vision and structured output capabilities:
    - Vision: Processes images via chat API with image_url content type
    - Structured: Uses chat.parse() for automatic Pydantic validation
    Recommended models:
    - pixtral-12b-latest: Fast inference, good for simple layouts
    - pixtral-large-latest: Advanced vision, complex layouts
    - mistral-medium-2508: Balanced performance
    - mistral-small-2506: Cost-effective, high volume
    """

    def __init__(self, api_key: str, model_name: str):
        """
        Initialize Mistral Vision provider.
        Args:
            api_key: Mistral API key
            model_name: Model identifier (e.g., "pixtral-12b-latest")
        """
        self.client = Mistral(api_key=api_key)
        self.model_name = model_name
        # Cache images to avoid re-converting same page
        self._image_cache: dict[tuple[Path, int], str] = {}

    def process_page(
        self,
        pdf_path: Path,
        page_num: int,  # 1-indexed
        schema_class: type[BaseModel],
        system_prompt: str,
        **kwargs
    ) -> dict:
        """
        Extract structured data from PDF page using vision model.
        This method combines vision and structured output capabilities:
        1. Converts PDF page to base64 image (vision input)
        2. Calls chat.parse() with Pydantic schema (structured output)
        3. Returns validated data automatically
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            schema_class: Pydantic model defining the extraction schema
            system_prompt: Extraction instructions (load from /prompts/*.txt)
            **kwargs: Additional options:
                - user_prompt: Optional user message (default: "Extract the data.")
                - dpi: Image resolution for PDF conversion (default: 200)
                - temperature: API temperature (default: 0)
                - max_tokens: Response limit (default: 4096)
        Returns:
            Extracted data dict with at least {"items": [...]}
            Data is automatically validated against schema_class
        Raises:
            ImportError: If pdf2image not installed
            RuntimeError: If PDF conversion or API call fails
        """
        # Convert PDF page to image (with caching)
        cache_key = (pdf_path, page_num)
        if cache_key not in self._image_cache:
            logger.debug(f"Converting page {page_num} of {pdf_path.name} to image")
            self._image_cache[cache_key] = pdf_page_to_base64_image(
                pdf_path,
                page_num,
                dpi=kwargs.get("dpi", 200)
            )

        image_url = self._image_cache[cache_key]

        # Get user prompt (optional)
        user_prompt = kwargs.get("user_prompt", "Extract and structure the text from the following magazine page, Your output should be an instance of a JSON object following the schema provided.")

        # Call chat.parse() with vision input and structured output
        logger.debug(f"Calling {self.model_name} for page {page_num}")

        try:
            resp = self.client.chat.parse(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": image_url
                            }
                        ]
                    }
                ],
                response_format=schema_class,  # Pydantic model for structured output
                temperature=kwargs.get("temperature", 0),  # 0 for consistent extraction
                max_tokens=kwargs.get("max_tokens", 4096)
            )

            # chat.parse() returns validated Pydantic model in resp.parsed
            # Convert to dict for compatibility with extraction pipeline
            return resp.parsed.model_dump()

        except Exception as e:
            logger.error(f"Vision API call failed for page {page_num}: {e}")
            raise RuntimeError(
                f"Failed to extract data from page {page_num} using {self.model_name}: {e}"
            ) from e