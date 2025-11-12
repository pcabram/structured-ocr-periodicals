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
    current = Path(__file__).resolve().parent

    # Check this directory and all parent directories
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent

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
    magazine_name: str,
    model_name: str,
    schema_name: str,
    prompt_name: str | None = None,
    base_root: Path | None = None
) -> Path:
    """
    Build standardized evaluation output path.

    Directory structure:
        base_root/{magazine}/model={model}/schema={schema}/prompt={prompt}/

    Args:
        magazine_name: Magazine/PDF name (e.g., "La_Plume")
        model_name: Model identifier (e.g., "pixtral-12b-latest")
        schema_name: Schema identifier (e.g., "stage1_page_v2")
        prompt_name: Prompt identifier (e.g., "detailed_v1"), None for OCR models
        base_root: Base directory (default: PREDICTIONS / "evaluations")

    Returns:
        Standardized path for extraction results

    Example:
        >>> out_root = build_evaluation_path(
        ...     magazine_name="La_Plume",
        ...     model_name="pixtral-12b-latest",
        ...     schema_name="stage1_page_v2",
        ...     prompt_name="detailed_v1"
        ... )
        >>> # Returns: data/predictions/evaluations/La_Plume/model=pixtral-12b-latest/schema=stage1_page_v2/prompt=detailed_v1
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

    magazine_clean = sanitize(magazine_name)
    model_clean = sanitize(model_name)
    schema_clean = sanitize(schema_name)

    # Build path with explicit dimension labels
    path = base_root / magazine_clean / f"model={model_clean}" / f"schema={schema_clean}"

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

    Searches for directories matching: base_root/{magazine}/model=*/schema=*/prompt=*

    Args:
        base_root: Base evaluation directory (default: PREDICTIONS / "evaluations")

    Returns:
        List of dicts with keys: magazine_name, model_name, schema_name, prompt_name, path, num_files

    Example:
        >>> results = discover_all_extractions()
        >>> for result in results:
        ...     print(f"{result['magazine_name']}: {result['model_name']} × {result['schema_name']} × {result['prompt_name']}")
    """
    if base_root is None:
        base_root = PREDICTIONS / "evaluations"

    if not base_root.exists():
        return []

    discovered = []

    # Find all directories matching: {magazine}/model=*/schema=*/prompt=*
    for result_dir in base_root.glob("*/model=*/schema=*/prompt=*"):
        if not result_dir.is_dir():
            continue

        # Check if results exist (JSON files)
        json_files = list(result_dir.rglob("*.json"))
        if not json_files:
            continue

        # Parse metadata from path
        parts = result_dir.parts

        # Find the magazine name
        magazine_name = None
        eval_idx = None
        for i, part in enumerate(parts):
            if part == "evaluations" and i + 1 < len(parts):
                magazine_name = parts[i + 1]
                break
    
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

        if magazine_name and model_name and schema_name:
            discovered.append({
                "magazine_name": magazine_name,
                "model_name": model_name,
                "schema_name": schema_name,
                "prompt_name": prompt_name,
                "path": result_dir,
                "num_files": len(json_files)
            })

    # Sort by magazine, then model, schema, prompt for consistency
    discovered.sort(key=lambda d: (
        d["magazine_name"],
        d["model_name"],
        d["schema_name"],
        d["prompt_name"] or ""
    ))

    return discovered


# ============================================================================
# SMART EXTRACTION LOGIC
# ============================================================================

def discover_available_magazines(src_root: Path | None = None) -> list[str]:
    """
    Discover all available magazine PDFs in the raw data directory.

    Args:
        src_root: Source directory with PDFs (default: RAW_DATA)

    Returns:
        List of magazine names (PDF filenames without .pdf extension)

    Example:
        >>> magazines = discover_available_magazines()
        >>> print(magazines)
        ['La_Plume', 'Le_Mercure_de_France', ...]
    """
    if src_root is None:
        src_root = RAW_DATA

    if not src_root.exists():
        return []

    # Find all PDF files
    pdf_files = src_root.rglob("*.pdf")

    # Extract magazine names (stem = filename without extension)
    # Use set to deduplicate (in case of subdirectories with same PDF names)
    magazines = sorted({pdf.stem for pdf in pdf_files})

    return magazines


def discover_existing_extractions(base_root: Path | None = None) -> set[tuple[str, str, str, str | None]]:
    """
    Discover what extractions already exist.

    Scans the evaluations directory and returns a set of tuples representing
    existing extractions: (magazine, model, schema, prompt)

    Args:
        base_root: Base evaluation directory (default: PREDICTIONS / "evaluations")

    Returns:
        Set of tuples: (magazine_name, model_name, schema_name, prompt_name)

    Example:
        >>> existing = discover_existing_extractions()
        >>> print(existing)
        {('La_Plume', 'mistral-ocr-latest', 'stage1_page_v2', None),
         ('La_Plume', 'pixtral-12b-latest', 'stage1_page_v2', 'detailed_v1'),
         ...}
    """
    # Use the existing discovery function
    all_results = discover_all_extractions(base_root)

    # Convert to set of tuples
    existing = {
        (r["magazine_name"], r["model_name"], r["schema_name"], r["prompt_name"])
        for r in all_results
    }

    return existing


def generate_all_combinations(
    magazines: list[str],
    models: list[str],
    schemas: list[str],
    prompts: list[str]
) -> set[tuple[str, str, str, str | None]]:
    """
    Generate all possible extraction combinations.

    Handles OCR models specially: they don't use prompts (prompt=None).
    Vision models: tested with all prompt variants.

    Args:
        magazines: List of magazine names
        models: List of model names
        schemas: List of schema names
        prompts: List of prompt names

    Returns:
        Set of tuples: (magazine_name, model_name, schema_name, prompt_name)

    Example:
        >>> combos = generate_all_combinations(
        ...     magazines=['La_Plume'],
        ...     models=['mistral-ocr-latest', 'pixtral-12b-latest'],
        ...     schemas=['stage1_page_v2'],
        ...     prompts=['detailed_v1']
        ... )
        >>> print(combos)
        {('La_Plume', 'mistral-ocr-latest', 'stage1_page_v2', None),
         ('La_Plume', 'pixtral-12b-latest', 'stage1_page_v2', 'detailed_v1')}
    """
    combinations = set()

    for magazine in magazines:
        for model in models:
            for schema in schemas:
                # Check if this is an OCR model
                is_ocr = 'ocr' in model.lower()

                if is_ocr:
                    # OCR models: one extraction per schema (no prompts)
                    combinations.add((magazine, model, schema, None))
                else:
                    # Vision models: require prompts
                    if not prompts:
                        raise ValueError(
                            f"Vision model '{model}' requires prompts, but none provided. "
                            f"Please specify at least one prompt variant."
                        )
                    # Test all prompts
                    for prompt in prompts:
                        combinations.add((magazine, model, schema, prompt))

    return combinations


def calculate_missing_extractions(
    magazines: list[str],
    models: list[str],
    schemas: list[str],
    prompts: list[str],
    base_root: Path | None = None
) -> set[tuple[str, str, str, str | None]]:
    """
    Calculate which extractions are missing.

    Compares what SHOULD exist (all combinations) with what DOES exist.
    Returns only the missing ones.

    Args:
        magazines: List of magazine names
        models: List of model names
        schemas: List of schema names
        prompts: List of prompt names
        base_root: Base evaluation directory (default: PREDICTIONS / "evaluations")

    Returns:
        Set of missing tuples: (magazine_name, model_name, schema_name, prompt_name)

    Example:
        >>> missing = calculate_missing_extractions(
        ...     magazines=['La_Plume'],
        ...     models=['mistral-ocr-latest'],
        ...     schemas=['stage1_page_v2'],
        ...     prompts=[]
        ... )
        >>> if missing:
        ...     print(f"{len(missing)} extraction(s) missing")
    """
    # What should exist
    expected = generate_all_combinations(magazines, models, schemas, prompts)

    # What does exist
    existing = discover_existing_extractions(base_root)

    # What's missing
    missing = expected - existing

    return missing

# Module self-test (runs when imported)

# Verify project structure on import
if not PROJECT_ROOT.exists():
    raise RuntimeError(f"Project root does not exist: {PROJECT_ROOT}")

if not (PROJECT_ROOT / "pyproject.toml").exists():
    raise RuntimeError(f"pyproject.toml not found in: {PROJECT_ROOT}")
