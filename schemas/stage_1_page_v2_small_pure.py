"""
Stage 1 Page Schema - Version 2 Small Pure (No Continuation Fields)
Pydantic model for page-level OCR extraction from historical French literary magazines.
This schema does NOT include continuation tracking fields.

CHANGES FROM V2 SMALL:
- Removed is_continuation field
- Removed continues_on_next_page field

Based on: docs/ontology.md v1.0
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# Item classification vocabulary
ITEM_CLASS = Literal["prose", "verse", "ad", "paratext", "unknown"]


class Stage1Item(BaseModel):
    """
    A discrete text block on the page (contribution, advertisement, or paratextual element).
    """
    
    item_class: ITEM_CLASS = Field(
        ...,
        description="Content type: prose, verse, ad, paratext, or unknown"
    )
    
    item_text_raw: str = Field(
        ...,
        description="Complete text as printed, preserving formatting and orthography"
    )
    
    item_title: Optional[str] = Field(
        None,
        description="Title or heading if printed"
    )
    
    item_author: Optional[str] = Field(
        None,
        description="Author name if printed"
    )


class Stage1PageModel(BaseModel):
    """
    Complete page-level extraction from a historical magazine page.
    Includes page metadata and all text items in reading order.
    """
    
    mag_title: Optional[str] = Field(
        None,
        description="Magazine title as printed"
    )
    
    issue_label: Optional[str] = Field(
        None,
        description="Issue number or label"
    )
    
    date_string: Optional[str] = Field(
        None,
        description="Publication date as printed"
    )
    
    page_ref: Optional[str] = Field(
        None,
        description="Page number"
    )
    
    items: List[Stage1Item] = Field(
        ...,
        description="All text blocks in reading order"
    )