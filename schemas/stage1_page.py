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
            "Complete text of this block exactly as printed.\n\n"
            "COMPLETENESS:\n"
            "Include ALL elements: title, subtitles, body text, author (beginning OR end), "
            "continuation markers (e.g., '(Suite)', '(À Suivre.)'), source attributions.\n\n"
            "CRITICAL - LINE BREAKS:\n"
            "For PROSE (articles, stories, essays):\n"
            "- Use \\n\\n ONLY for paragraph breaks (blank line or first-line indent in original)\n"
            "- DO NOT use \\n for visual line wraps in the printed layout\n"
            "- A continuous paragraph must be continuous text without line breaks\n"
            "- Common error: Adding \\n at every line wrap. DON'T DO THIS.\n"
            "- Exception: Use \\n for distinct visual elements like 'NUMÉRO 10\\n1er SEPTEMBRE 1889'\n\n"
            "For VERSE (poetry):\n"
            "- Preserve ALL line breaks exactly as printed\n"
            "- Each verse line = one line with \\n\n"
            "- Stanza breaks = \\n\\n\n"
            "- CRITICAL: If a verse line is too long and wraps to next line (often right-aligned), "
            "this is STILL THE SAME VERSE LINE. Join them without \\n. "
            "HYPHENATION:\n"
            "- REMOVE layout hyphens: 'extraordi-\\naire' becomes 'extraordinaire'\n"
            "- KEEP real hyphens: 'peut-être', 'vis-à-vis', 'celle-ci'\n"
            "- Common error: Keeping 'devant les-\\nquelles' instead of 'devant lesquelles'. "
            "Remove the hyphen AND join the words.\n\n"
            "ORTHOGRAPHY:\n"
            "- Preserve capitalization exactly (note: 19th century capitals often lack accents: 'A cette époque')\n"
            "- Preserve ALL accents as printed: è é ê à ù etc.\n"
            "- Preserve ligatures: œ, æ\n"
            "- Preserve quotation marks: « » or \" as printed\n"
            "- Preserve '&' if present\n"
            "- Preserve spacing around punctuation AS PRINTED (inconsistent in originals)"
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
            "Ordered list of ALL text blocks appearing on the page.\n\n"
            "CRITICAL: Extract EVERY piece of text visible on the page as a separate item. "
            "This includes:\n"
            "- Magazine masthead and title (even if already in mag_title field)\n"
            "- Issue information, dates, page numbers (even if in other fields)\n"
            "- Literary contributions (prose, verse)\n"
            "- Advertisements and announcements\n"
            "- Editorial content and notes\n"
            "- Printer information\n"
            "- Subscription forms\n"
            "- Running headers/footers\n"
            "- Section titles\n\n"
            "READING ORDER RULES:\n"
            "1. Direction: Top to bottom, left to right.\n"
            "2. Multi-column layouts: Complete left column entirely, then right column.\n"
            "3. CRITICAL - Column-spanning contributions: When a SINGLE contribution spans multiple columns, "
            "treat it as ONE item. Combine text from left column + right column in item_text_raw. "
            "DO NOT create separate items for each column of the same contribution. "
            "Common error: Splitting one poem/article into two items because of column break. DON'T DO THIS.\n"
            "4. Missing text: If text continues in a second column, you MUST include it. "
            "Do not omit the second half of contributions.\n"
            "5. Natural reading: Follow the sequence a reader would naturally follow.\n\n"
            "Empty pages: For blank pages, items may be empty list []."
        )
    )