# LexiSift

**Understand the vocabulary behind a book.**

LexiSift is a local-first EPUB vocabulary analyzer. The first release focuses on a small,
deterministic core: read an EPUB in its declared spine order, extract visible text, tokenize it,
and produce word-frequency statistics that remain useful when LexiSift later grows into a
multi-book vocabulary library.

## v0.1 features

- Reads EPUB metadata from `META-INF/container.xml` and the package OPF.
- Follows the EPUB `spine` instead of scanning XHTML files alphabetically.
- Extracts visible text from XHTML/HTML documents.
- Unicode-aware tokenization with normalized apostrophes and hyphens.
- Counts total occurrences and number of chapters containing each word.
- Exports:
  - `vocabulary.csv`
  - `chapters.csv`
  - `summary.txt`
- Runs entirely on the local laptop; no book content is uploaded anywhere.

## Requirements

- Python 3.12+

## Install for development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Analyze an EPUB

```bash
lexisift analyze book.epub
```

Choose another report directory:

```bash
lexisift analyze book.epub --output-dir output/my-book
```

Example console output:

```text
Title: Example Book
Author: Example Author
Chapters: 18
Total word tokens: 72451
Unique normalized words: 6284
Reports: /path/to/lexisift-output
```

`vocabulary.csv` has this shape:

```csv
word,count,chapter_count,percentage
the,4281,18,5.908821
child,417,15,0.575561
brain,296,12,0.408552
```

## Development checks

```bash
ruff check .
mypy src
pytest
```

## Roadmap

The core model is intentionally book-aware from the beginning. Planned milestones include:

1. stop-word filtering without losing raw statistics;
2. lemma and word-family analysis;
3. chapter progression and reading coverage;
4. SQLite-backed multi-book library;
5. `NEW / SEEN / LEARNING / KNOWN / IGNORED` vocabulary states;
6. previewing a new book against personal vocabulary history;
7. phrases/collocations and example sentences;
8. flashcard export;
9. optional local browser dashboard.

The raw per-book analysis remains inspectable/exportable even after SQLite becomes the primary
library store.
