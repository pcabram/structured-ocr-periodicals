"""
Centralized path management for the magazine OCR pipeline.

This module provides consistent path resolution across notebooks and scripts.

Usage in notebooks:
    from utils.paths import PROJECT_ROOT, RAW_DATA, PREDICTIONS, GOLD_CLEAN
    
    # Use paths directly
    pdfs = list(RAW_DATA.glob("*.pdf"))
    
Usage in scripts:
    from utils.paths import PROJECT_ROOT, ensure_data_dirs
    
    # Create necessary directories
    ensure_data_dirs()
"""
from pathlib import Path


def get_project_root() -> Path:
    """
    Find project root by locating pyproject.toml.
    
    Searches upward from this file's location until it finds a directory
    containing pyproject.toml.

    Returns:
        Path to project root directory
        
    Raises:
        RuntimeError: If pyproject.toml not found in any parent directory
    """
    # Start from this file's location
    current = Path(__file__).resolve()
    
    # Check this directory and all parent directories
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    
    # If we get here, we couldn't find the project root
    raise RuntimeError(
        "Could not find project root (no pyproject.toml found). "
        "Are you running from within the project directory?"
    )


# Project root

PROJECT_ROOT = get_project_root()

# Data directories

DATA_ROOT = PROJECT_ROOT / "data"
RAW_DATA = DATA_ROOT / "raw"
PREDICTIONS = DATA_ROOT / "predictions"
BNF_OCR = DATA_ROOT / "bnf_ocr"

# Gold standard directories

GOLD_STANDARD = DATA_ROOT / "gold_standard"
GOLD_RAW = GOLD_STANDARD / "raw"
GOLD_CLEAN = GOLD_STANDARD / "cleaned"


# Other project directories

DOCS = PROJECT_ROOT / "docs"
NOTEBOOKS = PROJECT_ROOT / "notebooks"
SCHEMAS = PROJECT_ROOT / "schemas"
UTILS = PROJECT_ROOT / "utils"


# Utility function for directory creation

def ensure_data_dirs() -> None:
    """
    Create data directories if they don't exist.
    
    Safe to call multiple times (idempotent). Creates:
    - data/raw/
    - data/predictions/
    - data/bnf_ocr/
    - data/gold_standard/raw/
    - data/gold_standard/cleaned/
    """
    directories = [
        RAW_DATA,
        PREDICTIONS,
        BNF_OCR,
        GOLD_RAW,
        GOLD_CLEAN,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Module self-test (runs when imported)

# Verify project structure on import
if not PROJECT_ROOT.exists():
    raise RuntimeError(f"Project root does not exist: {PROJECT_ROOT}")

if not (PROJECT_ROOT / "pyproject.toml").exists():
    raise RuntimeError(f"pyproject.toml not found in: {PROJECT_ROOT}")