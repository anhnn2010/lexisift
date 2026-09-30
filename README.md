# LexiSift

**Understand the vocabulary behind a book.**

LexiSift is a local, offline-first Python CLI for analyzing vocabulary in EPUB books. It follows the EPUB spine, classifies readable sections, tokenizes English text, groups conservative word families, separates common stop words, and reports cumulative reading coverage.

## Current version

`0.2.0`

## Requirements

- Python 3.12+

LexiSift uses `lemminflect` for offline English morphology. Its dictionary and runtime resources ship with the Python package, so no language model or corpus download is required at runtime. LexiSift deliberately uses dictionary lookups only and keeps ambiguous forms unchanged unless the book provides strong independent word-family evidence.

## Install for development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

If you use `pyenv` / `pyenv-virtualenv`, run `pyenv rehash` after installing so the `lexisift` command is available through pyenv shims.

## Analyze an EPUB

Analyze every readable spine section:

```bash
lexisift analyze book.epub
```

Analyze only the main reading content (Introduction + Chapters + Conclusion):

```bash
lexisift analyze book.epub --scope main
```

Choose an output directory:

```bash
lexisift analyze book.epub --scope main -o output/book
```

## Reports

LexiSift writes:

```text
output/book/
├── summary.txt
├── sections.csv
├── vocabulary.csv
├── content_words.csv
├── lemmas.csv
└── coverage.csv
```

### `sections.csv`

EPUB spine order, semantic section classification, inclusion state, and token counts.

### `vocabulary.csv`

Every normalized surface form with:

- `word`
- `lemma`
- `is_stopword`
- `count`
- `section_count`
- `first_seen_section`
- `percentage`

### `content_words.csv`

The same learning-oriented word statistics with common English stop words removed.

### `lemmas.csv`

Dictionary-form word-family aggregation, including observed forms. For example:

```text
child    <- child | children
run      <- run | runs | running
strategy <- strategy | strategies
```

LexiSift uses LemmInflect's packaged English lexical resources rather than suffix stemming. It prefers correctness over aggressive grouping: automatic dictionary grouping is limited to conservative regular inflections, while irregular forms are folded only through a small curated safe list. Ambiguous homographs such as `left`/`leave` and `saw`/`see` remain separate without contextual POS evidence. Dictionary-ambiguous regular forms remain unchanged unless an independent form in the same book supports one family. Lexical possessives such as `child's` are folded into their base word, while common apostrophe contractions remain intact.

### `coverage.csv`

Lemmas ranked by frequency with cumulative token coverage. This answers questions such as how much of the running text is covered by the 100, 500, 1000, or 2000 most frequent lemmas in the book.

## Section scope

`--scope all` preserves every readable EPUB spine document.

`--scope main` includes only sections classified as:

- Introduction
- Chapter
- Conclusion

Front matter, table of contents, acknowledgments, author biography, and other back matter remain visible in `sections.csv` but do not contribute to vocabulary statistics.

## Tokenization

LexiSift preserves ordinary apostrophes and lexical hyphens:

```text
don't
well-being
four-year-old
```

En/em dashes act as separators, and unusually long stylistic hyphen chains are split into words.

## Development checks

```bash
pytest
ruff check .
mypy src
```

## Roadmap

Planned later stages include:

- vocabulary progression by section/book
- known / learning / new vocabulary state
- multi-book SQLite library
- personalized reading coverage
- phrase and collocation analysis
- example sentence selection
- flashcard export
- KOReader reading-history integration
