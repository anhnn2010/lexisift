# LexiSift

**Understand the vocabulary behind a book.**

LexiSift is a local, offline-first Python CLI for analyzing vocabulary in EPUB books. It follows the EPUB spine, classifies readable sections, tokenizes English text, groups conservative word families, separates common stop words, reports cumulative reading coverage, and produces a transparent ranked list of repeated learning candidates.

## Current version

`0.3.0`

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

By default, `learning_words.csv` keeps content lemmas that occur at least 3 times. Adjust the threshold when needed:

```bash
lexisift analyze book.epub --scope main --learning-min-count 5 -o output/book
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
├── learning_words.csv
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

### `learning_words.csv`

A book-local candidate list intended for vocabulary review. It is grouped by lemma, excludes stop words, and by default removes lemmas that occur fewer than 3 times. Columns include:

- `rank`
- `lemma`
- `count`
- `section_count`
- `section_coverage_percentage`
- `first_seen_section`
- `book_percentage`
- `priority_score`
- `forms`

The priority score is intentionally simple and auditable:

```text
count * (1 + section_count / analyzed_sections)
```

Frequency remains the main signal, while vocabulary that recurs across more of the book receives a modest bonus. This is **not** yet a difficulty score: common words you already know can still rank highly until a personal known-word profile is added.

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

- known / learning / new vocabulary state
- vocabulary progression by section/book
- multi-book SQLite library
- personalized reading coverage
- phrase and collocation analysis
- example sentence selection
- flashcard export
- KOReader reading-history integration
