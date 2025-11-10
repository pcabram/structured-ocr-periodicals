"""
Shared utilities for model providers.
Internal module containing helper functions used by multiple providers.
"""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Literal


def encode_file_to_data_url(path: Path, mime: str = "application/pdf") -> str:
    """
    Encode file as base64 data URL.
    Args:
        path: Path to file
        mime: MIME type (default: "application/pdf")
    Returns:
        Data URL string in format: data:<mime>;base64,<encoded_content>
    Example:
        >>> pdf_url = encode_file_to_data_url(Path("doc.pdf"))
        >>> pdf_url.startswith("data:application/pdf;base64,")
        True
    """
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def pdf_page_to_base64_image(
    pdf_path: Path,
    page_num: int,  # 1-indexed
    image_format: Literal["PNG", "JPEG"] = "PNG",
    dpi: int = 200
) -> str:
    """
    Convert single PDF page to base64-encoded image.
    Required for vision models that don't accept PDF input directly.
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-indexed, first page = 1)
        image_format: Output image format ("PNG" or "JPEG")
        dpi: Resolution for conversion (default: 200)
    Returns:
        Data URL string in format: data:image/<format>;base64,<encoded>
    Raises:
        ImportError: If pdf2image package not installed
        RuntimeError: If PDF conversion fails
    Example:
        >>> img_url = pdf_page_to_base64_image(Path("doc.pdf"), page_num=1)
        >>> img_url.startswith("data:image/png;base64,")
        True
    Note:
        Requires pdf2image package and poppler system library.
        Install: pip install pdf2image
    """
    try:
        from pdf2image import convert_from_path
    except ImportError as e:
        raise ImportError(
            "pdf2image is required for vision models. "
            "Install with: pip install pdf2image"
        ) from e

    try:
        # Convert single page to image
        images = convert_from_path(
            pdf_path,
            first_page=page_num,
            last_page=page_num,
            dpi=dpi
        )

        if not images:
            raise RuntimeError(f"No image generated for page {page_num}")

        # Encode image to base64
        buffer = BytesIO()
        images[0].save(buffer, format=image_format)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Determine MIME type
        mime = f"image/{image_format.lower()}"

        return f"data:{mime};base64,{b64}"

    except Exception as e:
        raise RuntimeError(
            f"Failed to convert PDF page {page_num} to image: {e}"
        ) from e