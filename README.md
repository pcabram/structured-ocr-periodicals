# structured-ocr-for-periodicals

**AI-assisted structured extraction from historical French literary magazines**

A methodological demonstration of schema-guided OCR extraction using generative Vision Language Models (VLMs) applied to a historical French press corpus. This codebase was developed for the [Médias 19 Congress 2026](https://www.medias19.org/) (Montpellier, May 18-20, 2026).

## Overview

This project demonstrates how VLMs can extract structured, semantically-rich data from historical magazine pages while preserving textual fidelity. Rather than treating OCR as simple text extraction, we use the models' structured outputs capabilities to simultaneously perform content segmentation and classification, and metadata extraction in a single pass.

By providing the VLM with a detailed Pydantic schema describing our target data structure, we transform raw PDF pages into structured JSON annotations that segment the original content into individual contributions (items) with their associated metadata (authors, titles, continuation markers), along with page-level metadata.

## Repository contents

**Schemas** - 7 Pydantic model variants for different extraction granularities
**Utils** - Extraction pipeline, evaluation metrics, text processing
**Notebooks** - Complete workflow from PDF extraction to comparative evaluation (3 notebooks)
**Data** - Example corpus (*La Plume*), gold standard annotations, BnF OCR baseline
**Docs** - Data model specification and ontology

Click on project structure below for detailed file organization.

<details>
<summary>📁 Detailed file structure</summary>

```
structured-ocr-for-periodicals/
├── schemas/              # Pydantic models (7 variants)
├── utils/                # Extraction & evaluation pipeline
├── notebooks/            # Interactive workflows (01a-01c)
├── data/
│   ├── raw/              # Source PDFs
│   ├── gold_standard/    # Manual annotations
│   ├── bnf_ocr/          # BnF baseline
│   └── predictions/      # VLM outputs
├── docs/                 # Methodology & specifications
├── tests/                # Unit tests
└── prompts/              # System prompts for vision models
```

</details>

## Research context

This work is presented as part of the research for the PhD thesis *Poétiques individuelles et collectives dans les « Petites revues » fin-de-siècle : modéliser la cohésion des groupes littéraires par des mesures de similarité textuelle*, examining how LLMS and VLMs can benefit historical press studies through improved digitization and postprocessing methods.

**Application domain:** Fin-de-siècle French literary magazines (1880s-1900s), specifically artistic and literary magazines, such as *La Plume* (1889-1899) and similar periodicals from the Bibliothèque nationale de France (BnF) and other libraries and archives digitized collections.

**Research affiliation:** This work is conducted at École Normale Supérieure (Lattice, UMR 8094), École Doctorale 540, in collaboration with the BnF Département de la Découverte des collections et de l'accompagnement à la recherche and the Centre des Sciences des Littératures en langue Française of the Université Paris Nanterre, under the supervision of Thierry Poibeau (CNRS-ENS) and Julien Schuh (Université Paris Nanterre).

## Why this matters for historical press studies

Press corpus digitization faces two fundamental obstacles: the human cost of 
manual transcription and the insufficiency of traditional OCR tools, which produce 
high error rates requiring complex post-processing. For medium and large corpora, 
these limitations make full-text indexing and search practically impossible.

Beyond simple transcription challenges, the modeling of historical magazines presents some 
structural complexities:

### 1. **Complex multi-column layouts**
19th-century magazines mixed prose, poetry, advertisements and images in multi-column 
layouts with variable typography. Traditional OCR tools struggle with reading order in these highly variable and experimental layouts, often producing scrambled or incomplete text.

### 2. **Editorial continuity across pages**
Literary contributions frequently spanned multiple pages (sometimes across 
multiple issues). Identifying continuation points is essential for reconstructing 
complete texts and recreate accurate representations of issues and magazines. Currently, there are no tools in the market that could correctly segment and index these contents.

### 3. **Period, genre and language-specific characteristics**

Period-specific conventions must be correctly extracted and preserved as closely as possible, such as:
- **Spelling variants**: archaic forms, regional variations, historically absent accents on capital letters.
- **Conventions on the use of capitalization and small capitals**
- **Typographical particularities**: initial capitals, stylized text, writing intertwined with images, etc.

### 4. **Data enrichment**
Scholars need structured metadata, not just raw text, to adequately explore and exploit press corpora. In addition to its full, clean text, each contribution item requires:
- **Classification** (prose, verse, advertisement, paratext)
- **Metadata** (title, author attribution)
- **Continuation markers** for multi-page reconstruction

These structured elements enable downstream analyses: author network studies, 
textual circulation patterns, editorial practice evolution.

### 5. **Scale vs. resources**
Thousands of magazine issues exist in libraries' collections and archives, but manual transcription and annotation is prohibitively expensive. Traditional OCR provides raw text but loses semantic 
structure. Manual annotation preserves structure but doesn't scale. VLMs are expensive for large corpora.

## The VLM approach

**Schema-guided extraction:** by providing a VLM with a detailed Pydantic schema describing the target data structure, we perform OCR, layout analysis, content classification, and metadata extraction in a single API call. This eliminates the multi-stage pipeline typical of traditional OCR workflows.

### Key advantages

**1. Reduced postprocessing : single-pass extraction**  
Traditional OCR requires separate stages: image preprocessing → text recognition → layout analysis → content classification → metadata extraction. Each stage introduces errors that compound through the pipeline.

Traditional OCR outputs require extensive postprocessing:
- Manual or algorithmic layout segmentation
- Content classification (distinguishing prose from verse, advertisements from articles)
- Metadata field extraction (identifying and separating titles from authors)

With schema-guided extraction, these steps are handled simultaneously during extraction, not after. The structured output directly produces the target format (JSON with classified items and extracted metadata).

**2. Semantic awareness**
The model understands document structure: it can be informed that a title typically precedes body text, that author attributions appear at specific locations, and that line breaks matter for verse but not prose. This semantic understanding produces cleaner segmentation than purely visual layout analysis and offer endless possibilities of structured extraction.

### Implementation: Mistral Document AI

This pipeline uses [Mistral AI's Document AI API](https://docs.mistral.ai/capabilities/document_ai/annotations) with structured output generation.

**Why Mistral Document AI:**
- **Native structured outputs**: The API accepts Pydantic schemas and returns JSON conforming to those schemas.
- **Document-optimized**: Document AI models are specifically designed for document understanding and for handling complex layouts.
- **Multilingual capability**: Strong native performance on French historical texts with period-specific orthography.

**API workflow:**
1. PDF pages are encoded as base64 data URLs.
2. Pydantic schema is converted to JSON Schema format using `response_format_from_pydantic_model()`.
3. API call specifies: model (`mistral-ocr-latest`), document, page indices, and output schema.
4. Response contains structured JSON matching the schema specification.
5. Pydantic validates the output, ensuring type correctness.

See `utils/extraction.py` for complete implementation details.

### Performance

**Section under construction**

Evaluated on 34 pages from *La Plume* (November 15, 1893 issue) comparing schema-guided VLM extraction against BnF's traditional OCR baseline.

#### Evaluation method: Order-Agnostic Bag-of-Words

To fairly compare systems with different segmentation strategies, we use an order-agnostic bag-of-words approach. This measures vocabulary identification accuracy (whether the system correctly identifies the words present on each page) regardless of extraction order or item boundaries.

**Why order-agnostic?** Traditional OCR tools doen't typically structure content, and different VLMs extractions may segment content differently yet still validly (e.g., reading columns in different sequences). Order-agnostic evaluation focuses purely on OCR quality.

#### Results: Word-level coverage

**F1 Score (word identification):**
- Mistral VLM: **91.5%**
- BnF OCR: **81.8%**

**Precision** (% of extracted words that are correct):
- Mistral: **91.5%**
- BnF: **80.5%**

**Recall** (% of gold standard words successfully extracted):
- Mistral: **92.3%**
- BnF: **84.4%**

**Per-page averages (569 words/page in gold standard):**
- Mistral: 322 correct, 27 missed, 26 hallucinated
- BnF: 295 correct, 54 missed, 74 hallucinated

#### Results: Character-Level Coverage

**F1 Score (character identification, letters only normalization):**
- Mistral: **96.3%**
- BnF: **95.6%**

At the character level, both systems perform similarly. The VLM's advantage appears primarily in word boundary detection and handling of complex typography.

#### Structure detection (Beyond OCR Quality)

**Item matching:** 52.9% of gold standard items successfully matched to predicted items (similarity threshold ≥ 0.75)

The VLM correctly identifies about half of the individual contribution boundaries. This is the most challenging aspect, not character recognition, but semantic segmentation of the content within complex multi-column layouts.

---

For complete evaluation methodology and metrics across all 5 dimensions (structure, text, classification, metadata, continuations), see `utils/evaluation.py` and `notebooks/01c_evaluation.ipynb`.

### Methodological contributions

**1. Schema-driven pipeline architecture**
The extraction logic is decoupled from the schema specification. Adding new fields or modifying extraction granularity requires only changing the Pydantic schema definition. This design is transferable to other document types, languages, and historical periods.

**2. Schema variants for empirical comparison for prompt engineering**
7 Pydantic schema variants with different field granularities enable empirical evaluation of quality-cost trade-offs and explore the model's performance under instructions of varying detail. This systematic comparison (see `notebooks/01c_evaluation.ipynb`) reveals how instruction complexity affects extraction quality.

Common structure across variants is documented in `docs/ontology.md`.

**3. Multi-dimensional evaluation framework**  
Systematic assessment across 5 dimensions:
- **Structure detection**: Item matching and segmentation accuracy
- **Text quality**: Character/word error rates (order-agnostic and structure-aware)
- **Classification accuracy**: Content type identification (prose, verse, advertisement, paratext)
- **Metadata extraction**: Title and author field precision/recall
- **Continuation tracking**: Cross-page relationship detection

**4. Reproducible gold standard corpus**  
48 manually annotated pages from *La Plume* (1889-1893) following ethe data model specified in `docs/ontology.md`. This reference corpus enables:
- Systematic quality evaluation
- Future model fine-tuning
- Comparison with other extraction methods (demonstrated with BnF OCR baseline)

## Installation

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- Mistral AI API key ([free with limits](https://console.mistral.ai/api-keys/))

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/structured-ocr-for-periodicals.git
cd structured-ocr-for-periodicals

# Install dependencies
poetry install

# Configure API key
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY

# Activate environment
poetry shell
```

## Usage

This project is designed to be used interactively through Jupyter notebooks. The 6 notebooks provide a complete workflow from extraction to comparative evaluation.

### Notebooks workflow

**01a. Extraction** (`notebooks/01a_extraction.ipynb`)

Extract pages from PDFs using configurable schema variants. This notebook demonstrates the complete extraction pipeline, including:
- Single-page and batch extraction
- Multiple schema variant support
- Configurable model and prompt settings
- Output validation and statistics

Start here to understand the extraction process and generate predictions for evaluation.

**01b. Gold Standard Creation** (`notebooks/01b_gold_standard_creation.ipynb`)

Interactive workflow for creating manual annotations. Shows how the reference corpus was built, using VLM output as pre-annotation and human manual correction.

**01c. Comprehensive Evaluation** (`notebooks/01c_evaluation.ipynb`)

Complete evaluation framework with multi-dimensional metrics and comparative analysis:

- **Single-schema evaluation**: Detailed assessment across all 5 dimensions (structure detection, text quality, classification accuracy, metadata extraction, continuation tracking)
- **Comparative evaluation**: Side-by-side comparison of different extraction systems (e.g., Mistral VLM vs BnF OCR baseline)
- **Multi-schema evaluation**: Aggregate analysis across schema variants to identify optimal configurations for different use cases
- **Word and character coverage**: Bag-of-words metrics with multiple normalization strategies

### Recommended first steps


1. Review `docs/ontology.md` to understand the data model and schema structure.
2. Open `01a_extraction.ipynb` and run it to extract a test PDF with your chosen schema variant.
3. Examine the generated JSON output in `data/predictions/`.
4. Open `01c_evaluation.ipynb` to see comprehensive evaluation metrics and comparative analysis.

## Data Model

Each extracted page produces a JSON file with this structure:
```json
{
  "mag_title": "LA PLUME",
  "issue_label": "N° 10",
  "date_string": "1er Septembre 1889",
  "page_ref": "100",
  "items": [
    {
      "item_class": "verse",
      "item_text_raw": "STÉRILITÉS\n\nCautérise et coagule...",
      "item_title": "STÉRILITÉS",
      "item_author": "Jules Laforgue",
      "is_continuation": false,
      "continues_on_next_page": true
    }
  ]
}
```

**Some key features:**
- **Page-level metadata**: Magazine title, issue, date, page number as printed.
- **Structured items**: Each text block classified and segmented.
- **Preserved orthography**: Original 19th-century spelling, capitalization, punctuation maintained exactly.
- **Reading order**: Items should appear in natural reading sequence (top-to-bottom, left-to-right for multi-column layouts).
- **Continuation tracking**: Optional fields signal multi-page contributions for future reconstruction.

**Item classification:**
- `prose` - Articles, essays, short stories, reviews...
- `verse` - Poetry.
- `ad` - Advertisements.
- `paratext` - Mastheads, section headers, tables of contents, subscription talons.
- `unknown` - Ambiguous content.

See `docs/ontology.md` for complete field definitions and annotation principles.

## License

MIT License

## Contact

Pedro Cabrera Ramírez  
École Normale Supérieure (Lattice, UMR 8094)  
Email: pedro.cabrera.ramirez@ens.psl.eu