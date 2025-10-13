"""
Stage 1 Page Schema - WITH Continuation Fields

Pydantic model for page-level OCR extraction from historical French literary magazines.
This schema includes continuation tracking fields for multi-page contributions.

Based on: docs/ontology.md v1.0
"""

from typing import List, Optional, Literal
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
            "Classification of the text block's content type:\n"
            "- 'prose': Continuous prose text (articles, essays, short stories, reviews, "
            "literary criticism, chronicles). Characterized by paragraph structure.\n"
            "- 'verse': Poetry with line breaks and potential stanza structure. "
            "Includes both measured and free verse.\n"
            "- 'ad': Advertisements and commercial content. Book announcements, "
            "publisher advertisements, commercial announcements.\n"
            "- 'paratext': Editorial framing and metadata. Magazine title/masthead, "
            "section headers, table of contents, running headers/footers, page numbers, "
            "printer information, editor/manager information, subscription notices, "
            "pricing information for the magazine itself, portrait/illustration announcements.\n"
            "- 'unknown': Classification uncertain. Use only when genuinely ambiguous. "
            "Prefer specific classifications when possible.\n\n"
            "Classification is based on content nature, not structural position on page."
        )
    )
    
    item_text_raw: str = Field(
        ...,
        description=(
            "Complete text of this block exactly as printed on the page.\n\n"
            "TRANSCRIPTION RULES:\n"
            "Completeness: Include ALL printed elements for this item: title (if above text), "
            "body text, author attribution (if exists, whether at beginning or end), subtitles, "
            "continuation markers (e.g., '(Suite)'), source attributions. "
            "Do NOT include text from other items.\n\n"
            "Line Breaks:\n"
            "- For verse (poetry): Preserve all line breaks exactly as printed. "
            "Each line of the poem is a separate line. Preserve stanza breaks (double line breaks).\n"
            "- For prose: Use line breaks ONLY for paragraph breaks. "
            "Do not preserve line wraps from the printed page layout. "
            "A continuous paragraph should be continuous text.\n\n"
            "Hyphenation:\n"
            "- Remove line-end word breaks: Words hyphenated across lines should be joined. "
            "Example: 'extraordi-\\naire' becomes 'extraordinaire'.\n"
            "- Keep genuine hyphens: Compound words retain their hyphens. "
            "Examples: 'peut-être', 'vis-à-vis'.\n\n"
            "Orthography:\n"
            "- Preserve original capitalization exactly as printed.\n"
            "- Preserve accents as printed.\n"
            "- Preserve archaic or variant spellings.\n"
            "- Preserve spacing around punctuation as printed."
        )
    )
    
    item_title: Optional[str] = Field(
        None,
        description=(
            "Title or heading of the contribution, if printed. "
            "Extract even if displayed in decorative, display, or non-standard font. "
            "Transcribe exactly as printed. "
            "Set to null if no title is present. "
            "Note: Title should also appear in item_text_raw."
        )
    )
    
    item_author: Optional[str] = Field(
        None,
        description=(
            "Author name(s) attributed to this contribution, if printed. "
            "Author attribution may appear at the BEGINNING or at the END of the contribution. "
            "For multiple authors, transcribe as printed (e.g., 'Edmond et Jules de Goncourt'). "
            "Preserve name format variations (e.g., 'Jules Laforgue', 'J. Laforgue', 'Laforgue'). "
            "Set to null if no author attribution is present. "
            "Note: Author should also appear in item_text_raw."
        )
    )
    
    is_continuation: Optional[bool] = Field(
    None,
    description=(
        "Indicates whether this item continues from the previous page.\n\n"
        "Set to true if evidence strongly suggests this is a continuation:\n"
        "- Text starts with lowercase letter (mid-sentence)\n"
        "- No title present when one would be expected for this item type\n"
        "- Text clearly begins mid-paragraph or mid-thought\n\n"
        "Omit this field entirely if the item does NOT continue from previous page. "
        "Evidence suggests that the text starts a new contribution and it's not a continuation:\n"
        "- Text starts with capital letter and appears to be beginning of sentence\n"
        "- Title is present\n"
        "- Content appears self-contained\n\n"
        "Note: An item can be BOTH a continuation from previous page AND continue to next page. "
        "In this case, both is_continuation and continues_on_next_page will be true.\n\n"
        "Never set to false - absence of field indicates no continuation."
    )
)

    continues_on_next_page: Optional[bool] = Field(
        None,
        description=(
            "Indicates whether this item continues to the next page.\n\n"
            "Set to true if evidence strongly suggests continuation follows:\n"
            "- Text ends mid-sentence with no closing punctuation\n"
            "- No author attribution at the end when expected for this item type\n"
            "- Narrative or argument clearly incomplete\n\n"
            "Evidence that suggests the contribution is complete and doesn't continue in the next page:\n"
            "- Text ends with closing punctuation (period, exclamation, question mark)\n"
            "- Author attribution present at end\n"
            "- Content appears complete (story ends, poem concludes, article reaches conclusion)\n\n"
            "Omit this field entirely if the item does NOT continue to next page. "
            "Note: An item can be BOTH a continuation from previous page AND continue to next page. "
            "In this case, both is_continuation and continues_on_next_page will be true.\n\n"
            "Never set to false - absence of field indicates no continuation."
        )
    )


class Stage1PageModel(BaseModel):
    """
    Complete page-level extraction from a historical magazine page.
    Includes page metadata and all text items in reading order.
    """
    
    mag_title: Optional[str] = Field(
        None,
        description=(
            "Magazine title as printed on this specific page. "
            "Transcribe exactly as it appears, even if stylized or in decorative font. "
            "Usually found in masthead, running header, or decorative logo. "
            "Set to null if not visible on this page."
        )
    )
    
    issue_label: Optional[str] = Field(
        None,
        description=(
            "Issue number or label as printed on the page. "
            "Preserve original formatting and language. "
            "May include year, volume, or series information. "
            "Examples: 'N° 10', 'Première année', 'Tome II, N° 5'. "
            "Set to null if not present on this page."
        )
    )
    
    date_string: Optional[str] = Field(
        None,
        description=(
            "Publication date as printed on this page. "
            "Preserve original formatting - do not standardize or modernize. "
            "Keep period-appropriate orthography. "
            "Examples: 'Juin 89.', '1er Septembre 1889', '15 juin 1890'. "
            "Set to null if not present on this page."
        )
    )
    
    page_ref: Optional[str] = Field(
        None,
        description=(
            "Page number as printed on this page. "
            "Transcribe exactly as formatted. "
            "Examples: '100', 'p. 45', '- 23 -'. "
            "Set to null if not present."
        )
    )
    
    items: List[Stage1Item] = Field(
        ...,
        description=(
            "Ordered list of all text blocks appearing on the page.\n\n"
            "READING ORDER RULES:\n"
            "1. Direction: Top to bottom, left to right.\n"
            "2. Multi-column layouts: Complete the entire left column before moving to the right column. "
            "Do not interleave between columns.\n"
            "3. Column-spanning content: A single contribution may span multiple columns. "
            "When this occurs, treat the entire contribution as ONE item, with the text from "
            "the left column followed by the text from the right column in item_text_raw. "
            "Do NOT split a single contribution into multiple items based on column breaks.\n"
            "4. Completeness: Include all visible text on the page. "
            "This includes: masthead, section headers, running headers/footers, contributions, "
            "advertisements, printer information.\n"
            "5. Natural order: Follow the sequence a human reader would naturally follow. "
            "Maintain the flow of continuous reading.\n\n"
            "The items list should contain all text blocks visible on the page. "
            "For blank pages or pages with no extractable text, items may be an empty list []."
        )
    )