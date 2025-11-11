"""
Model provider abstraction for document extraction.
Supports multiple AI providers (Mistral, OpenAI, etc.) with a unified interface.
Usage:
    from pathlib import Path
    from utils.providers import get_model_provider
    from schemas.stage1_page_v2 import Stage1PageModel

    # OCR model
    provider = get_model_provider("mistral-ocr-latest")
    result = provider.process_page(pdf_path, page_num=1, schema_class=Stage1PageModel)

    # Vision model (requires system_prompt)
    prompt = Path("prompts/stage1_page_v2.txt").read_text()
    provider = get_model_provider("pixtral-12b-latest")
    result = provider.process_page(
        pdf_path, page_num=1,
        schema_class=Stage1PageModel,
        system_prompt=prompt
    )    
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .base import ModelProvider
from .mistral_ocr import MistralOCRProvider
from .mistral_vision import MistralVisionProvider

if TYPE_CHECKING:
    from pathlib import Path

# Provider registry: maps model name to provider class
PROVIDER_REGISTRY: dict[str, type[ModelProvider]] = {
    # OCR models (native PDF support)
    "mistral-ocr-latest": MistralOCRProvider,

    # Vision models (image-based with structured outputs)
    "pixtral-12b-latest": MistralVisionProvider,
    "pixtral-large-latest": MistralVisionProvider,
    "mistral-medium-2508": MistralVisionProvider,
    "mistral-small-2506": MistralVisionProvider,    
}


def get_model_provider(
    model_name: str,
    api_key: str | None = None,
) -> ModelProvider:
    """
    Factory function to create provider for given model.
    Args:
        model_name: Model identifier (e.g., "mistral-ocr-latest")
        api_key: Optional API key (uses config if not provided)
    Returns:
        ModelProvider instance ready to process pages
    Raises:
        ValueError: If model not supported
    Example:
        >>> from utils.providers import get_model_provider
        >>> provider = get_model_provider("mistral-ocr-latest")
        >>> result = provider.process_page(pdf_path, page_num=1, schema_class=MySchema)
    """
    if model_name not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Model '{model_name}' not supported. "
            f"Available models: {available}"
        )

    provider_class = PROVIDER_REGISTRY[model_name]

    # Get API key from config if not provided
    if api_key is None:
        from utils.config import MISTRAL_CONFIG
        api_key = MISTRAL_CONFIG.get_api_key()

    return provider_class(api_key=api_key, model_name=model_name)


# Public exports
__all__ = [
    "ModelProvider",
    "MistralOCRProvider",
    "MistralVisionProvider"
    "get_model_provider",
    "PROVIDER_REGISTRY",
]