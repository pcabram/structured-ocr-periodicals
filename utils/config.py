"""
Configuration management for the magazine OCR pipeline.

Handles API keys, extraction parameters, and evaluation thresholds.

Usage:
    from utils.config import MISTRAL_CONFIG, EXTRACTION_CONFIG, EVALUATION_CONFIG
    
    client = Mistral(api_key=MISTRAL_CONFIG.get_api_key())
    matches = match_items(gold, pred, EVALUATION_CONFIG.similarity_threshold)
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .paths import PROJECT_ROOT

# Load environment variables from .env file if present
load_dotenv()


@dataclass(frozen=True)
class MistralConfig:
    """Mistral API configuration."""
    
    model_name: str = "mistral-ocr-latest"
    api_key_env: str = "MISTRAL_API_KEY"
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 8.0
    
    def get_api_key(self) -> str:
        """
        Get API key from environment variable or api_key file.
        
        Returns:
            API key string
            
        Raises:
            RuntimeError: If API key not found
        """
        # Try environment variable first
        key = os.environ.get(self.api_key_env)
        if key:
            return key.strip()
        
        # Fall back to api_key file
        key_file = PROJECT_ROOT / "api_key"
        if key_file.exists():
            return key_file.read_text(encoding="utf-8").strip()
        
        raise RuntimeError(
            f"{self.api_key_env} not set and {key_file} not found. "
            f"Set environment variable or create api_key file in project root."
        )


@dataclass(frozen=True)
class ExtractionConfig:
    """OCR extraction configuration."""
    
    overwrite: bool = False
    zero_pad: int = 3


@dataclass(frozen=True)
class EvaluationConfig:
    """Evaluation metric configuration."""
    
    # Item matching: 0.7 calibrated on La_Plume sample pages
    # Lower = more false matches, higher = missed valid matches
    similarity_threshold: float = 0.7
    
    # Metadata matching: higher threshold for short strings
    metadata_similarity_threshold: float = 0.8


# Singleton instances
MISTRAL_CONFIG = MistralConfig()
EXTRACTION_CONFIG = ExtractionConfig()
EVALUATION_CONFIG = EvaluationConfig()