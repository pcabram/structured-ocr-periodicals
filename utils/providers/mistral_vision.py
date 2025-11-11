"""
Mistral Vision provider implementation.
Provides document extraction using Mistral's vision models with image input
and structured output parsing.
Supports models: pixtral-12b-latest, pixtral-large-latest, mistral-medium-2508,
mistral-small-2506, and other vision-capable Mistral models.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from pydantic import BaseModel, ValidationError
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
        Uses JSON mode with manual validation for better error recovery.
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
                - max_tokens: Response limit (default: 8192)
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
                max_tokens=kwargs.get("max_tokens", 8192)
            )

        except Exception as e:
            logger.error(f"Vision API call failed for page {page_num}: {e}")
            raise RuntimeError(
                f"Failed to extract data from page {page_num} using {self.model_name}: {e}"
            ) from e
        
        # Extract raw JSON string
        raw_content = resp.choices[0].message.content

        # Log raw content length for debugging
        logger.debug(f"Received {len(raw_content)} characters of JSON content for page {page_num}")

        # Parse JSON manually
        try:
            result_dict = json.loads(raw_content)
            logger.debug(f"Parsed JSON successfully for page {page_num}")
        
        except json.JSONDecodeError as e:
            # JSON parsing failed - log details for debugging
            logger.error(f"JSON parsing failed for page {page_num}: {e}")
            logger.debug(f"Error location: line {e.lineno}, column {e.colno}, char {e.pos}")

            # Log a snippet around the error location
            start = max(0, e.pos - 100)
            end = min(len(raw_content), e.pos + 100)
            snippet = raw_content[start:end]
            logger.error(f"JSON snippet around error:\n{snippet}")

            # Log first 500 chars for context
            logger.debug(f"First 500 chars of raw JSON:\n{raw_content[:500]}")

            # Save the malformed JSON to a file for inspection
            error_file = Path(f"debug_json_error_page{page_num}.json")
            try:
                error_file.write_text(raw_content, encoding='utf-8')
                logger.error(f"Full malformed JSON saved to: {error_file}")
            except Exception as save_error:
                logger.warning(f"Could not save malformed JSON: {save_error}")

            raise RuntimeError(
                f"Failed to parse JSON from page {page_num}. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}. "
                f"Check {error_file} for full content."
            ) from e
    
        # Validate against Pydantic schema
        try:
            validated = schema_class(**result_dict)
            logger.debug(f"Successfully validated against schema for page {page_num}")
            
        except ValidationError as e:
            # Schema validation failed - log details
            logger.error(f"Schema validation failed for page {page_num}: {e}")
            logger.error(f"Validation errors: {e.errors()}")
            
            # Log the parsed dict structure
            logger.debug(f"Parsed dict keys: {result_dict.keys()}")
            if "items" in result_dict:
                logger.debug(f"Number of items: {len(result_dict['items'])}")
            
            raise RuntimeError(
                f"Data from page {page_num} does not match expected schema: {e}"
            ) from e
        
        # Return as dict
        return validated.model_dump()