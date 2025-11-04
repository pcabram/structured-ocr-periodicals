"""
Stage 1 Page Schema - Version 2 Medium
Pydantic model for page-level OCR extraction from historical French literary magazines.
This schema includes continuation tracking fields for multi-page contributions.

CHANGES FROM V2 IMPROVED:
- Condensed field descriptions to 2-3 sentences
- Removed section headers and bullet lists
- Kept critical warnings inline
- Removed most examples and defensive notes

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
        description=(
            "Classification of the text block: 'prose' for articles/stories/essays with paragraph structure, "
            "'verse' for poetry with line breaks, 'ad' for advertisements and commercial content, "
            "'paratext' for editorial framing (magazine title, issue number, date, page number, section headers, "
            "running headers/footers, printer info, subscription notices - CREATE A SEPARATE ITEM for each distinct element), "
            "or 'unknown' if genuinely ambiguous."
        ),
    )
    
    item_text_raw: str = Field(
        ...,
        description=(
            "Complete text exactly as printed. If this contribution spans multiple columns, include ALL text from all columns in this single item. "
            "For prose, use \\n\\n only for paragraph breaks, not for visual line wraps. For verse, preserve all line breaks exactly. "
            "Remove layout hyphens (extraordi-naire → extraordinaire) but keep real hyphens (peut-être). "
            "Preserve 19th century orthography (capitals without accents), all accents, ligatures, and spacing as printed. "
            "Include all elements: title, body, author (check end of text - authors commonly appear there), continuation markers, attributions."
        ),
    )
    
    item_title: Optional[str] = Field(
        None,
        description="Title or heading of the contribution if printed, transcribed exactly. Set to null if absent."
    )
    
    item_author: Optional[str] = Field(
        None,
        description=(
            "Author name(s) if printed - check both beginning AND end of text (authors most commonly at end). "
            "Transcribe exactly as printed."
        ),
    )
    
    is_continuation: Optional[bool] = Field(
        None,
        description=(
            "Set to true if this item continues from the previous page (starts lowercase/mid-sentence, no title when expected, mid-paragraph). "
            "Omit field entirely if not a continuation - never set to false."
        ),
    )
    
    continues_on_next_page: Optional[bool] = Field(
        None,
        description=(
            "Set to true if this item continues to the next page (ends mid-sentence, no closing punctuation, no author at end when expected, incomplete narrative). "
            "Omit field entirely if item is complete - never set to false."
        ),
    )


class Stage1PageModel(BaseModel):
    """
    Complete page-level extraction from a historical magazine page.
    Includes page metadata and all text items in reading order.
    """
    
    mag_title: Optional[str] = Field(
        None,
        description="Magazine title as printed on this page, transcribed exactly. Set to null if not visible."
    )
    
    issue_label: Optional[str] = Field(
        None,
        description="Issue number or label as printed, preserving original formatting. Set to null if absent."
    )
    
    date_string: Optional[str] = Field(
        None,
        description="Publication date as printed, preserving original formatting. Set to null if absent."
    )
    
    page_ref: Optional[str] = Field(
        None,
        description="Page number as printed, transcribed exactly. Set to null if absent."
    )
    
    items: List[Stage1Item] = Field(
        ...,
        description=(
            "Ordered list of all text blocks on the page in reading order (top-to-bottom, left-to-right). "
            "CRITICAL: If a single contribution spans multiple columns, treat it as ONE item - combine all text in item_text_raw, don't split into separate items. "
            "Extract every piece of visible text including magazine masthead, issue info, dates, page numbers, literary contributions, ads, editorial content, printer info, subscription forms, headers/footers, section titles. "
            "Empty pages may have empty list."
        ),
    )