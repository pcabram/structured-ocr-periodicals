# Stage 1 Ontology: Page-Level OCR Extraction

**Version:** 1.0
**Date:** October 13, 2025
**Context:** Historical Fin-de-siècle French literary magazine digitization

---

## Purpose

This document defines the data model and annotation principles for Stage 1 of the magazine digitization pipeline. Stage 1 extracts structured information from individual magazine pages using OCR, preserving page-level granularity for subsequent issue reconstruction (Stage 2) and knowledge graph construction (Stage 3).

---

## Data Model

### Page-Level Fields

Each page is represented as a JSON object with the following top-level fields:

#### `mag_title` (optional string)

The magazine title as printed on this specific page.

**Guidelines:**
- Transcribe exactly as it appears, even if stylized or in decorative font.
- Usually found in: masthead, running header, or decorative logo.
- May vary in formatting across pages (full title vs. abbreviated).
- Set to `null` if not visible on this page.

**Examples:**
- `"LA PLUME"`
- `"La Plume - Revue Littéraire"`

---

#### `issue_label` (optional string)

Issue number or label as printed on the page.

**Guidelines:**
- Preserve original formatting and language.
- May include year, volume, or series information.
- Set to `null` if not present on this page.

**Examples:**
- `"N° 10"`
- `"Première année"`
- `"Tome II, N° 5"`

---

#### `date_string` (optional string)

Publication date as printed on this page.

**Guidelines:**
- Preserve original formatting. Do not standardize or modernize.
- Keep period-appropriate orthography.
- Set to `null` if not present on this page.

**Examples:**
- `"Juin 89."`
- `"1er Septembre 1889"`
- `"15 juin 1890"`

---

#### `page_ref` (optional string)

Page number as printed on this page.

**Guidelines:**
- Transcribe exactly as formatted.
- Set to `null` if not present.

**Examples:**
- `"100"`
- `"p. 45"`
- `"- 23 -"`

---

#### `items` (required list)

An ordered list of all text blocks appearing on the page.

**Reading Order Rules:**

1. **Direction:** Top to bottom, left to right.
2. **Multi-column layouts:** 
   - Complete the entire left column before moving to the right column.
   - Do not interleave between columns.
3. **Column-spanning content:**
   - A single contribution may span multiple columns.
   - Read left column portion, then right column portion.
4. **Completeness:** 
   - Include all visible text on the page.
   - This includes: masthead, section headers, running headers/footers, contributions, advertisements, printer information.
5. **Natural order:**
   - Follow the sequence a human reader would naturally follow.
   - Maintain the flow of continuous reading.

**Requirement:** The `items` list should contain all text blocks visible on the page. For blank pages or pages with no extractable text, `items` may be an empty list `[]`.

---

### Item-Level Fields

Each item in the `items` list represents a discrete text block and contains the following fields:

#### `item_class` (required enumeration)

Classification of the text block's content type.

**Allowed values:**

- **`prose`**: Continuous prose text.
  - Articles, essays, short stories, reviews, literary criticism, chronicles...
  - Characterized by paragraph structure.

- **`verse`**: Poetry.
  - Poems with line breaks and that may have a stanza structure.
  - Includes both measured and free verses but not prose poems.

- **`ad`**: Advertisements and commercial content.
  - Book announcements, publisher advertisements, commercial announcements.
  - Might include images. Only transcribe text.

- **`paratext`**: Editorial framing and metadata.
  - Magazine title/masthead.
  - Section headers (e.g., "CHRONIQUE LITTÉRAIRE", "POÉSIE").
  - Table of contents.
  - Running headers and footers.
  - Page numbers when separate from body text.
  - Printer information (e.g., "Imprimerie...").
  - Editor/manager information (e.g., "Le Gérant: ...").
  - Subscription notices, pricing information for the magazine itself.
  - Portrait/illustration announcements.

- **`unknown`**: Classification uncertain.
  - Use only when genuinely ambiguous.
  - Prefer specific classifications when possible.

**Note:** Classification is based on content nature, not structural position on page.

---

#### `item_text_raw` (required string)

The complete text of this block exactly as printed on the page.

**Transcription Principles:**

**Completeness:**
- Include ALL printed elements for this item:
  - Title (if it appears above the text).
  - The body text.
  - Author attribution (if it appears wether be it at the end or in the beginning of the text).
  - Subtitles, continuation markers (e.g., "(Suite)").
  - Source attributions (e.g., "(Les Paradis.)").
- Do NOT include text from other items.

**Line Breaks:**
- **For verse (poetry):** Preserve all line breaks exactly as printed.
  - Each line of the poem is a separate line in the transcription.
  - Preserve stanza breaks (double line breaks).
- **For prose:** Use line breaks ONLY for paragraph breaks.
  - Do not preserve line wraps from the printed page layout.
  - A continuous paragraph should be continuous text.

**Hyphenation:**
- **Remove line-end word breaks:** Words hyphenated across lines should be joined.
  - Printed: `"extraordi-\naire"`.
  - Transcribed: `"extraordinaire"`.
- **Keep genuine hyphens:** Compound words retain their hyphens.
  - Examples: `"peut-être"`, `"vis-à-vis"`, `"chef-d'œuvre"`, `"au-dessus"`.

**Orthography:**
- Preserve original capitalization exactly as printed.
- Preserve accents as printed.
  - This includes the historical absence of accents on capital letters (e.g., `"STERILITIES"` not `"STÉRILITÉS"`).
- Preserve archaic or variant spellings.
- Preserve spacing around punctuation as printed (as French typography often includes spaces before punctuation).

**Examples:**

*Verse item:*
```
STÉRILITÉS

Cautérise et coagule
En vigules
Ses lagunes des cerises
Des félines Ophélies
Orphelines en folie.

Jules Laforgue.

(Imitation de Notre-Dame la Lune.)
```

*Prose item with continuation:*
```
LES POLICHINELLES

(Suite)

IV

Où l'auteur se permet une irrévérencieuse monographie des Revues et des Revuistes.

Les Revuïstes, espèces de naïfs qui prennent pour des paroles d'évangile...

(À Suivre.)

Léon Deschamps.
```

---

#### `item_title` (optional string)

Title or heading of the contribution, if printed.

**Guidelines:**
- Extract even if displayed in decorative, display, or non-standard font.
- Transcribe exactly as printed.
- Set to `null` if no title is present.
- Note: Title should also appear in `item_text_raw`.

**Examples:**
- `"STÉRILITÉS"`
- `"SONNET"`
- `"LES POLICHINELLES"`
- `"Chronique de la quinzaine"`

---

#### `item_author` (optional string)

Author name(s) attributed to this contribution, if printed.

**Guidelines:**
- Author attribution may appear at the beginning or end of the contribution
- For multiple authors, transcribe as printed (e.g., `"Edmond et Jules de Goncourt"`).
- Preserve name format variations (e.g., `"Jules Laforgue"`, `"J. Laforgue"`, `"Laforgue"`).
- Set to `null` if no author attribution is present.
- Note: Author should also appear in `item_text_raw`.

**Examples:**
- `"Jules Laforgue"`
- `"Henri de Régnier"`
- `"Léon Deschamps"`

**Rationale:** Separating the author into its own field enables entity reconciliation in Stage 3, even though it's also preserved in the raw text.

---

#### `is_continuation` (optional boolean)

Indicates whether this item continues from the previous page.

**Values:**
- `true`: Evidence strongly suggests this is a continuation.
- Absent from JSON: Item does NOT continue from previous page.

**Do not include this field when the item is not a continuation.** Absence indicates the item starts on this page.

**Evidence to include field with `true`:**
- Text starts with lowercase letter (mid-sentence).
- No title present when one would be expected for this item type.
- Text clearly begins mid-paragraph or mid-thought.
- Explicit continuation markers (e.g., "(Suite)").

**Evidence field should be absent:**
- Text starts with capital letter and appears to be beginning of sentence.
- Title is present.
- Content appears self-contained.

**Note:** An item can be BOTH a continuation from previous page AND continue to next page. In this case, both `is_continuation` and `continues_on_next_page` will be present and set to `true`.

---

#### `continues_on_next_page` (optional boolean)

Indicates whether this item continues to the next page.

**Values:**
- `true`: Evidence strongly suggests continuation follows.
- Absent from JSON: Item does NOT continue to next page.

**Do not include this field when the item is complete.** Absence indicates the item ends on this page.

**Evidence to include field with `true`:**
- Text ends mid-sentence with no closing punctuation.
- No author attribution at the end when expected for this item type.
- Narrative or argument clearly incomplete.
- Explicit continuation markers (e.g., "(À Suivre.)").

**Evidence field should be absent:**
- Text ends with closing punctuation (period, exclamation, question mark).
- Author attribution present at end.
- Content appears complete (story ends, poem concludes, article reaches conclusion).

**Note:** An item can be BOTH a continuation from previous page AND continue to next page. In this case, both `is_continuation` and `continues_on_next_page` will be present and set to `true`.

---

## Design Rationale

### Why Page-Level Granularity?

Stage 1 maintains page-level separation because:
1. **Fidelity:** Preserves original pagination for scholarly reference.
2. **Flexibility:** Allows reconstruction strategies to vary by document type in Stage 2.
3. **Parallelization:** Pages can be processed independently.
4. **Error isolation:** Problems on one page don't corrupt entire issues.
5. **Selective reprocessing:** Individual pages can be re-extracted without reprocessing entire documents.

### Why Separate Metadata Fields?

Fields like `item_title` and `item_author` are extracted separately (in addition to appearing in `item_text_raw`) because:
1. **Entity reconciliation:** Stage 3 links authors to external databases (BnF, IdRef, VIAF, Wikidata).
2. **Searchability:** Structured fields enable direct queries.
3. **Variation handling:** Authors may be named differently across contributions.
4. **Completeness:** Raw text preserves original layout for verification.

### Why Continuation Fields?

The `is_continuation` and `continues_on_next_page` fields serve as probabilistic signals for Stage 2 reconstruction:
1. **Stitching hints:** Help identify multi-page contributions.
2. **Validation:** Allow checking whether reconstruction succeeded.
3. **Ambiguity:** `null` values indicate genuinely uncertain cases.
4. **Experimental:** Their utility will be evaluated empirically.

---

## Version History

- **v1.0** (2025-10-13): Initial ontology definition.

---

## References

This ontology supports the doctoral research project on fin-de-siècle French literary magazine networks. For implementation details, see:
- `schemas/stage1_page.py` - Pydantic model implementation.
- `notebooks/00_gold_standard_creation.ipynb` - Gold standard annotation workflow.
- `notebooks/01_extraction.ipynb` - Extraction implementation.