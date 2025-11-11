"""
Extraction Utilities for Stage 1 OCR
Abstracts Mistral Document AI API calls and PDF processing logic.
Used by notebooks for single-schema and batch extraction.
"""
from __future__ import annotations
import json
import base64
import logging
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from pypdf import PdfReader
from pydantic import BaseModel, ValidationError
from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from tqdm.auto import tqdm

logger = logging.getLogger("extraction")


# ============================================================================
# PDF PROCESSING
# ============================================================================

def count_pages(pdf_path: Path) -> int:
    """
    Count number of pages in a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Number of pages (0 if file cannot be read)
    """
    try:
        with pdf_path.open("rb") as fh:
            try:
                reader = PdfReader(fh, strict=False)
            except TypeError:
                reader = PdfReader(fh)  # fallback if 'strict' arg unsupported
            
            if getattr(reader, "is_encrypted", False) and reader.decrypt("") == 0:
                logger.warning(f"Encrypted PDF (cannot decrypt): {pdf_path.name}")
                return 0
            
            return len(reader.pages)
    except Exception as e:
        logger.warning(f"Could not read {pdf_path.name}: {e}")
        return 0


def encode_file_to_data_url(path: Path, mime: str = "application/pdf") -> str:
    """
    Encode file as base64 data URL for Mistral API.
    
    Args:
        path: Path to file
        mime: MIME type
        
    Returns:
        Data URL string (data:<mime>;base64,<encoded_content>)
    """
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


# ============================================================================
# API RESPONSE HANDLING
# ============================================================================

def parse_annotation_response(resp) -> dict:
    """
    Extract annotation dict from Mistral OCR response.
    
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


def call_with_retry(
    fn: Callable[[], Any],
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0
) -> Any:
    """
    Call function with exponential backoff retry logic.
    
    Args:
        fn: Function to call (no arguments)
        retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        
    Returns:
        Function result
        
    Raises:
        Exception: If all retries fail
    """
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if attempt == retries - 1:
                raise
            
            delay = min(max_delay, base_delay * (2 ** attempt))
            jitter = delay * (1 + 0.25 * random.random())
            
            logger.warning(f"API call failed ({e}). Retrying in {jitter:.1f}s...")
            time.sleep(jitter)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_extraction(
    annot: dict,
    schema_class: type[BaseModel],
    page_number: int,
    pdf_name: str
) -> tuple[bool, List[str]]:
    """
    Validate extracted annotation for common issues.
    
    Args:
        annot: Annotation dictionary
        schema_class: Pydantic model class for schema validation
        page_number: Page number (1-indexed)
        pdf_name: PDF filename for logging
        
    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []
    
    # Check if items exist
    if "items" not in annot:
        warnings.append("Missing 'items' field")
        return False, warnings
    
    items = annot["items"]
    
    # Check for empty pages (valid but worth noting)
    if len(items) == 0:
        warnings.append("Zero items extracted (possibly blank page)")
    
    # Check for suspiciously short items
    for idx, item in enumerate(items):
        text = item.get("item_text_raw", "")
        if len(text) < 3:
            warnings.append(f"Item {idx} has very short text ({len(text)} chars)")
    
    # Schema validation with Pydantic
    try:
        schema_class(**annot)
    except ValidationError as e:
        warnings.append(f"Schema validation failed: {e}")
        return False, warnings
    
    return True, warnings


# ============================================================================
# CORE EXTRACTION
# ============================================================================

def _extract_pdf_pages_with_provider(



    pdf_path: Path,


    schema_class: type[BaseModel],


    model_name: str,


    out_root: Path,


    overwrite: bool = False,


    zero_pad: int = 3,


    max_retries: int = 3,


    base_delay: float = 1.0,


    max_delay: float = 8.0,


    src_root: Optional[Path] = None


) -> Dict[str, int]:


    """


    Extract PDF pages using provider architecture.





    Internal function - use extract_pdf_pages() with use_providers=True instead.


    """


    from .providers import get_model_provider





    # Initialize provider


    provider = get_model_provider(model_name)





    # Count pages


    n_pages = count_pages(pdf_path)


    if n_pages == 0:


        logger.warning(f"No pages found in {pdf_path.name}")


        return {"written": 0, "skipped": 0, "failed": 0, "total": 0}





    # Setup output directory


    if src_root:


        rel_path = pdf_path.relative_to(src_root).with_suffix("")


    else:


        rel_path = pdf_path.with_suffix("")





    out_dir = out_root / rel_path


    out_dir.mkdir(parents=True, exist_ok=True)





    # Statistics


    stats = {"written": 0, "skipped": 0, "failed": 0, "total": n_pages}





    # Pre-scan: find which pages need extraction


    pages_to_extract = []


    for page_idx in range(n_pages):


        page_num = page_idx + 1


        out_json = out_dir / f"{pdf_path.stem}__page-{page_num:0{zero_pad}d}.json"





        if not out_json.exists() or overwrite:


            pages_to_extract.append(page_num)  # 1-indexed for provider


        else:


            stats["skipped"] += 1





    # Log summary


    logger.info(


        f"Processing {pdf_path.name}: "


        f"{len(pages_to_extract)} to extract, "


        f"{stats['skipped']} already exist"


    )





    # Skip if nothing to do


    if len(pages_to_extract) == 0:


        logger.info(f"✓ {pdf_path.name}: All pages already extracted")


        return stats





    # Create progress bar


    page_iterator = tqdm(pages_to_extract, desc=f"  {pdf_path.name}", leave=False)





    for page_num in page_iterator:


        out_json = out_dir / f"{pdf_path.stem}__page-{page_num:0{zero_pad}d}.json"





        # Skip if exists and not overwriting


        if out_json.exists() and not overwrite:


            stats["skipped"] += 1


            continue





        # Call provider with retry logic


        try:


            def _call():


                return provider.process_page(


                    pdf_path=pdf_path,


                    page_num=page_num,


                    schema_class=schema_class


                )





            annot = call_with_retry(


                _call,


                retries=max_retries,


                base_delay=base_delay,


                max_delay=max_delay,


            )





        except Exception as e:


            logger.error(f"Page {page_num} failed after {max_retries} retries: {e}")


            stats["failed"] += 1


            continue





        # Ensure items key exists


        if "items" not in annot:


            annot["items"] = []





        # Validate (but don't block writing)


        is_valid, warnings = validate_extraction(annot, schema_class, page_num, pdf_path.name)


        if warnings:


            for warning in warnings:


                logger.warning(f"Page {page_num}: {warning}")





        # Write output


        try:


            out_json.write_text(


                json.dumps(annot, ensure_ascii=False, indent=2),


                encoding="utf-8"


            )


            stats["written"] += 1





        except Exception as e:


            logger.error(f"Failed to write {out_json.name}: {e}")


            stats["failed"] += 1





    # Log summary


    logger.info(


        f"✓ {pdf_path.name}: "


        f"{stats['written']} written, "


        f"{stats['skipped']} skipped, "


        f"{stats['failed']} failed"


    )





    return stats

def extract_pdf_pages(
    pdf_path: Path,
    schema_class: type[BaseModel],
    client: Optional[Mistral],
    out_root: Path,
    model_name: str = "mistral-ocr-latest",
    overwrite: bool = False,
    zero_pad: int = 3,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    use_providers: bool = False,
    src_root: Optional[Path] = None
) -> Dict[str, int]:
    """
    Extract structured data from all pages of a PDF using a given schema.
    
    Creates one JSON file per page in:
    out_root / <pdf_name> / <pdf_name>__page-001.json
    
    Args:
        pdf_path: Path to PDF file
        schema_class: Pydantic model class for schema (e.g., Stage1PageModel)
        client: Mistral API client (only required if use_providers=False)
        out_root: Root directory for output
        model_name: Mistral model to use
        overwrite: Whether to overwrite existing files
        zero_pad: Number of digits for page numbering
        max_retries: Maximum API retry attempts
        base_delay: Initial retry delay
        max_delay: Maximum retry delay
        src_root: Source root directory (for relative path calculation)
        use_providers: If True, use provider architecture (default: False)
        
    Returns:
        Dict with statistics: {"written": n, "skipped": n, "failed": n, "total": n}
    """
    # Route to appropriate extraction method
    if use_providers:
        logger.info(f"Using provider architecture for extraction with model: {model_name}")
        return _extract_pdf_pages_with_provider(
            pdf_path=pdf_path,
            schema_class=schema_class,
            model_name=model_name,
            out_root=out_root,
            overwrite=overwrite,
            zero_pad=zero_pad,
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            src_root=src_root
        )
    
    # Legacy implementation without providers
    if client is None:
        raise ValueError("Client parameter must be provided when use_providers=False")

    logger.info(f"Using legacy extraction with model: {model_name}")

    # Count pages
    n_pages = count_pages(pdf_path)
    if n_pages == 0:
        logger.warning(f"No pages found in {pdf_path.name}")
        return {"written": 0, "skipped": 0, "failed": 0, "total": 0}
    
    # Setup output directory
    if src_root:
        rel_path = pdf_path.relative_to(src_root).with_suffix("")
    else:
        rel_path = pdf_path.with_suffix("")
    
    out_dir = out_root / rel_path
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Encode PDF
    data_url = encode_file_to_data_url(pdf_path)
    
    # Generate response format from schema
    doc_annot_fmt = response_format_from_pydantic_model(schema_class)
    
    # Statistics
    stats = {"written": 0, "skipped": 0, "failed": 0, "total": n_pages}
    
    # Pre-scan: find which pages need extraction
    pages_to_extract = []
    for page_idx in range(n_pages):
        page_num = page_idx + 1
        out_json = out_dir / f"{pdf_path.stem}__page-{page_num:0{zero_pad}d}.json"
        
        if not out_json.exists() or overwrite:
            pages_to_extract.append(page_idx)
        else:
            stats["skipped"] += 1

    # Log summary
    logger.info(
        f"Processing {pdf_path.name}: "
        f"{len(pages_to_extract)} to extract, "
        f"{stats['skipped']} already exist"
    )
    
    # Skip if nothing to do
    if len(pages_to_extract) == 0:
        logger.info(f"✓ {pdf_path.name}: All pages already extracted")
        return stats

    # Create progress bar
    page_iterator = tqdm(pages_to_extract, desc=f"  {pdf_path.name}", leave=False)

    
    for page_idx in page_iterator:
        page_num = page_idx + 1
        out_json = out_dir / f"{pdf_path.stem}__page-{page_num:0{zero_pad}d}.json"
        
        # Skip if exists and not overwriting
        if out_json.exists() and not overwrite:
            stats["skipped"] += 1
            continue
        
        # Call API with retry logic
        try:
            def _call():
                return client.ocr.process(
                    model=model_name,
                    document={"type": "document_url", "document_url": data_url},
                    pages=[page_idx],
                    document_annotation_format=doc_annot_fmt,
                    include_image_base64=False,
                )
            
            resp = call_with_retry(
                _call,
                retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
            )
            
        except Exception as e:
            logger.error(f"Page {page_num} failed after {max_retries} retries: {e}")
            stats["failed"] += 1
            continue
        
        # Parse response
        annot = parse_annotation_response(resp) or {}
        
        # Ensure items key exists
        if "items" not in annot:
            annot["items"] = []
        
        # Validate (but don't block writing)
        is_valid, warnings = validate_extraction(annot, schema_class, page_num, pdf_path.name)
        if warnings:
            for warning in warnings:
                logger.warning(f"Page {page_num}: {warning}")
        
        # Write output
        try:
            out_json.write_text(
                json.dumps(annot, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            stats["written"] += 1
            
        except Exception as e:
            logger.error(f"Failed to write {out_json.name}: {e}")
            stats["failed"] += 1
    
    # Log summary
    logger.info(
        f"✓ {pdf_path.name}: "
        f"{stats['written']} written, "
        f"{stats['skipped']} skipped, "
        f"{stats['failed']} failed"
    )
    
    return stats


def extract_all_pdfs(
    src_root: Path,
    schema_class: type[BaseModel],
    client: Mistral,
    out_root: Path,
    model_name: str = "mistral-ocr-latest",
    overwrite: bool = False,
    zero_pad: int = 3,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    use_providers: bool = False
) -> Dict[str, int]:
    """
    Extract all PDFs in source directory using a given schema.
    
    Args:
        src_root: Source directory containing PDFs
        schema_class: Pydantic model class for schema
        client: Mistral API client
        out_root: Root directory for output
        model_name: Mistral model to use
        overwrite: Whether to overwrite existing files
        zero_pad: Number of digits for page numbering
        max_retries: Maximum API retry attempts
        base_delay: Initial retry delay
        max_delay: Maximum retry delay
        
    Returns:
        Combined statistics across all PDFs
    """
    pdfs = sorted([p for p in src_root.rglob("*.pdf") if p.is_file()])
    
    if not pdfs:
        logger.warning(f"No PDF files found in {src_root}")
        return {"written": 0, "skipped": 0, "failed": 0, "total": 0}
    
    logger.info(f"Found {len(pdfs)} PDF(s) to process")
    
    # Accumulate statistics
    total_stats = {"written": 0, "skipped": 0, "failed": 0, "total": 0}
    
    for pdf_path in pdfs:
        stats = extract_pdf_pages(
            pdf_path=pdf_path,
            schema_class=schema_class,
            client=client,
            out_root=out_root,
            model_name=model_name,
            overwrite=overwrite,
            zero_pad=zero_pad,
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            src_root=src_root,
            use_providers=use_providers
        )
        
        for key in total_stats:
            total_stats[key] += stats[key]
    
    # Final summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total pages:   {total_stats['total']}")
    print(f"  Written:     {total_stats['written']}")
    print(f"  Skipped:     {total_stats['skipped']}")
    print(f"  Failed:      {total_stats['failed']}")
    print("=" * 60)
    
    return total_stats