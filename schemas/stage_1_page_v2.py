"""
Stage 1 Page Schema - Version 2 (Improved)
Pydantic model for page-level OCR extraction from historical French literary magazines.
This schema includes continuation tracking fields for multi-page contributions.

CHANGES FROM V1:
- Clarified paratext granularity: separate items for each element
- Reorganized item_text_raw: critical rules first
- Reorganized items reading order: column-spanning rule first
- Simplified item_author description

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
            "Classification of the text block's content type:\n"
            "- 'prose': Continuous prose text (articles, essays, short stories, reviews, "
            "literary criticism, chronicles). Characterized by paragraph structure.\n"
            "- 'verse': Poetry with line breaks and potential stanza structure. "
            "Includes both measured and free verse.\n"
            "- 'ad': Advertisements and commercial content. Book announcements, "
            "publisher advertisements, commercial announcements.\n"
            "- 'paratext': Editorial framing and metadata. CREATE A SEPARATE ITEM for each distinct paratextual element:\n"
            "  * Magazine title/masthead → separate item (even if in mag_title field)\n"
            "  * Issue number → separate item (even if in issue_label field)\n"
            "  * Date → separate item (even if in date_string field)\n"
            "  * Page number → separate item (even if in page_ref field)\n"
            "  * Section header → separate item\n"
            "  * Running header/footer → separate item\n"
            "  * Printer information → separate item\n"
            "  * Subscription notice → separate item\n"
            "  * Portrait/illustration announcement → separate item\n"
            "  Even if these elements appear close together visually, extract each as its own item.\n"
            "- 'unknown': Classification uncertain. Use only when genuinely ambiguous. "
            "Prefer specific classifications when possible.\n\n"
            "Classification is based on content nature, not structural position on page."
        ),
    )
    
    item_text_raw: str = Field(
        ...,
        description=(
            "Complete text of this block exactly as printed.\n\n"
            "CRITICAL RULES (MOST IMPORTANT):\n"
            "1. Multi-column text: If this contribution spans multiple columns, include ALL text from all columns in this single item\n"
            "2. Paragraph breaks in prose: Use \\n\\n ONLY for actual paragraph breaks (blank line or indent), NOT for visual line wraps\n"
            "3. Hyphenation: REMOVE layout hyphens (extraordi-naire → extraordinaire), KEEP real hyphens (peut-être, vis-à-vis)\n\n"
            "FORMAT BY CONTENT TYPE:\n"
            "For PROSE (articles, stories, essays):\n"
            "- Use \\n\\n only for paragraph breaks\n"
            "- Do NOT use \\n for line wraps in printed layout\n"
            "- Exception: Use \\n for distinct visual elements ('NUMÉRO 10\\n1er SEPTEMBRE 1889')\n\n"
            "For VERSE (poetry):\n"
            "- Preserve ALL line breaks exactly: each verse line = one \\n\n"
            "- Stanza breaks = \\n\\n\n"
            "- CRITICAL: If a verse line wraps to next line (often right-aligned), it's STILL ONE line - join without \\n\n\n"
            "PRESERVE EXACTLY AS PRINTED:\n"
            "- 19th century orthography: capitals often lack accents ('A cette époque' not 'À cette époque')\n"
            "- All accents: è é ê à ù\n"
            "- Ligatures: œ æ\n"
            '- Quotation marks: « » or " as printed\n'
            "- Ampersands: &\n"
            "- Spacing around punctuation (inconsistent in originals, preserve as-is)\n\n"
            "INCLUDE ALL ELEMENTS:\n"
            "- Title, subtitles, body text\n"
            "- Author (check beginning AND end of text - most commonly at END)\n"
            "- Continuation markers ('Suite', 'À Suivre')\n"
            "- Source attributions"
        ),
    )
    
    item_title: Optional[str] = Field(
        None,
        description=(
            "Title or heading of the contribution, if printed.\n"
            "Extract even if displayed in decorative, display, or non-standard font.\n"
            "Transcribe exactly as printed.\n"
            "Set to null if no title is present.\n"
            "Note: Title should also appear in item_text_raw."
        ),
    )
    
    item_author: Optional[str] = Field(
        None,
        description=(
            "Author name(s) if printed. CRITICAL: Check BOTH beginning and end of text - authors most commonly appear at the END.\n\n"
            "Transcribe exactly as printed. Examples: 'Edmond et Jules de Goncourt', 'Jules Laforgue', 'J. Laforgue'.\n\n"
            "Note: Author must also appear in item_text_raw."
        ),
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
        ),
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
        ),
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
        ),
    )
    
    issue_label: Optional[str] = Field(
        None,
        description=(
            "Issue number or label as printed on the page. "
            "Preserve original formatting and language. "
            "May include year, volume, or series information. "
            "Examples: 'N° 10', 'Première année', 'Tome II, N° 5'. "
            "Set to null if not present on this page."
        ),
    )
    
    date_string: Optional[str] = Field(
        None,
        description=(
            "Publication date as printed on this page. "
            "Preserve original formatting - do not standardize or modernize. "
            "Keep period-appropriate orthography. "
            "Examples: 'Juin 89.', '1er Septembre 1889', '15 juin 1890'. "
            "Set to null if not present on this page."
        ),
    )
    
    page_ref: Optional[str] = Field(
        None,
        description=(
            "Page number as printed on this page. "
            "Transcribe exactly as formatted. "
            "Examples: '100', 'p. 45', '- 23 -'. "
            "Set to null if not present."
        ),
    )
    
    items: List[Stage1Item] = Field(
        ...,
        description=(
            "Ordered list of ALL text blocks appearing on the page.\n\n"
            "READING ORDER & EXTRACTION RULES:\n"
            "1. CRITICAL - Column-spanning: If a single contribution spans multiple columns, treat it as ONE item. Combine all text from all columns in item_text_raw. Do NOT split one contribution into multiple items.\n"
            "2. Extract in natural reading order: top-to-bottom, left-to-right\n"
            "3. Multi-column layouts: Complete left column, then right column\n"
            "4. Include ALL text: Don't omit text that continues in additional columns\n\n"
            "EXTRACT EVERY piece of text visible on the page as a separate item:\n"
            "- Magazine masthead and title (even if in mag_title field)\n"
            "- Issue information, dates, page numbers (even if in other fields)\n"
            "- Literary contributions (prose, verse)\n"
            "- Advertisements and announcements\n"
            "- Editorial content and notes\n"
            "- Printer information\n"
            "- Subscription forms\n"
            "- Running headers/footers\n"
            "- Section titles\n\n"
            "Empty pages: items may be empty list []."
        ),
    )