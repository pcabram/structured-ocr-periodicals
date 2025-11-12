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


# ============================================================================
# EVALUATION PATH UTILITIES
# ============================================================================

def build_evaluation_path(
    model_name: str,
    schema_name: str,
    prompt_name: str | None = None,
    base_root: Path | None = None
) -> Path:
    """
    Build standardized evaluation output path.

    Directory structure:
        base_root/model={model}/schema={schema}/prompt={prompt}/

    Args:
        model_name: Model identifier (e.g., "pixtral-12b-latest")
        schema_name: Schema identifier (e.g., "stage1_page_v2")
        prompt_name: Prompt identifier (e.g., "detailed_v1"), None for OCR models
        base_root: Base directory (default: PREDICTIONS / "evaluations")

    Returns:
        Standardized path for extraction results

    Example:
        >>> out_root = build_evaluation_path(
        ...     model_name="pixtral-12b-latest",
        ...     schema_name="stage1_page_v2",
        ...     prompt_name="detailed_v1"
        ... )
        >>> # Returns: data/predictions/evaluations/model=pixtral-12b-latest/schema=stage1_page_v2/prompt=detailed_v1
    """
    import re

    if base_root is None:
        base_root = PREDICTIONS / "evaluations"

    # Sanitize names (replace spaces, special chars with underscores)
    def sanitize(name: str) -> str:
        # Replace spaces and special chars with underscores
        sanitized = re.sub(r'[^\w\-.]', '_', name)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        return sanitized.strip('_')

    model_clean = sanitize(model_name)
    schema_clean = sanitize(schema_name)

    # Build path with explicit dimension labels
    path = base_root / f"model={model_clean}" / f"schema={schema_clean}"

    # Add prompt dimension if provided (vision models)
    if prompt_name:
        prompt_clean = sanitize(prompt_name)
        path = path / f"prompt={prompt_clean}"
    else:
        # OCR models don't use prompts - use special marker
        path = path / "prompt=none"

    return path


def discover_all_extractions(base_root: Path | None = None) -> list[dict]:
    """
    Discover all extraction result directories.

    Searches for directories matching: base_root/model=*/schema=*/prompt=*

    Args:
        base_root: Base evaluation directory (default: PREDICTIONS / "evaluations")

    Returns:
        List of dicts with keys: model_name, schema_name, prompt_name, path

    Example:
        >>> results = discover_all_extractions()
        >>> for result in results:
        ...     print(f"{result['model_name']} × {result['schema_name']} × {result['prompt_name']}")
    """
    if base_root is None:
        base_root = PREDICTIONS / "evaluations"

    if not base_root.exists():
        return []

    discovered = []

    # Find all directories matching: model=*/schema=*/prompt=*
    for result_dir in base_root.glob("model=*/schema=*/prompt=*"):
        if not result_dir.is_dir():
            continue

        # Check if results exist (JSON files)
        json_files = list(result_dir.rglob("*.json"))
        if not json_files:
            continue

        # Parse metadata from path
        parts = result_dir.parts
        model_name = None
        schema_name = None
        prompt_name = None

        for part in parts:
            if part.startswith("model="):
                model_name = part[6:]
            elif part.startswith("schema="):
                schema_name = part[7:]
            elif part.startswith("prompt="):
                prompt_value = part[7:]
                prompt_name = None if prompt_value == "none" else prompt_value

        if model_name and schema_name:
            discovered.append({
                "model_name": model_name,
                "schema_name": schema_name,
                "prompt_name": prompt_name,
                "path": result_dir,
                "num_files": len(json_files)
            })

    # Sort by model, schema, prompt for consistency
    discovered.sort(key=lambda d: (d["model_name"], d["schema_name"], d["prompt_name"] or ""))

    return discovered

# Module self-test (runs when imported)

# Verify project structure on import
if not PROJECT_ROOT.exists():
    raise RuntimeError(f"Project root does not exist: {PROJECT_ROOT}")

if not (PROJECT_ROOT / "pyproject.toml").exists():
    raise RuntimeError(f"pyproject.toml not found in: {PROJECT_ROOT}")
