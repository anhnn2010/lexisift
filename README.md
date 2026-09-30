# LexiSift

**Understand the vocabulary behind a book.**

LexiSift is a local-first EPUB vocabulary analyzer. It reads an EPUB in declared spine order,
classifies its readable sections, extracts visible text, tokenizes it, and produces inspectable
word-frequency reports. The core is intentionally designed to grow into a multi-book personal
vocabulary library later.

## v0.1.1 features

- Reads EPUB metadata from `META-INF/container.xml` and the package OPF.
- Follows the EPUB `spine` instead of scanning XHTML files alphabetically.
- Treats spine documents as **sections**, not automatically as chapters.
- Classifies common section types using EPUB semantics first and conservative fallbacks second.
- Supports two analysis scopes:
  - `all`: all readable spine sections (default, compatible with v0.1 behavior)
  - `main`: introduction + chapters + conclusion
- Extracts visible text from XHTML/HTML documents.
- Unicode-aware tokenization:
  - preserves apostrophes and lexical hyphens (`don't`, `well-being`);
  - treats en/em dashes as separators;
  - splits unusually long stylistic hyphen chains.
- Counts total occurrences, section spread, and the first section where each word appears.
- Records token count for every spine section.
- Exports:
  - `vocabulary.csv`
  - `sections.csv`
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

If using `pyenv`, run `pyenv rehash` after installing so the `lexisift` command shim is refreshed.

## Analyze an EPUB

Analyze every readable spine section:

```bash
lexisift analyze book.epub
```

Analyze only the main reading content:

```bash
lexisift analyze book.epub --scope main
```

Choose another report directory:

```bash
lexisift analyze book.epub --scope main --output-dir output/my-book
```

Example console output:

```text
Title: Example Book
Author: Example Author
Scope: main
Spine sections: 18
Main chapters: 12
Analyzed sections: 14
Total word tokens: 68740
Unique normalized words: 6012
Reports: /path/to/lexisift-output
```

`vocabulary.csv` has this shape:

```csv
word,count,section_count,first_seen_section,percentage
the,4281,14,3,6.228397
child,417,12,3,0.606634
brain,296,11,4,0.430608
```

`sections.csv` makes classification and filtering inspectable:

```csv
order,section_id,type,included,token_count,title,href
1,toc,toc,no,142,Contents,OEBPS/toc.xhtml
2,intro,introduction,yes,1840,Introduction,OEBPS/intro.xhtml
3,c01,chapter,yes,5211,CHAPTER 1,OEBPS/c01.xhtml
```

## Development checks

```bash
ruff check .
mypy src
pytest
```

## Roadmap

The next language-aware layer will build on the cleaned section/token model:

1. stop-word filtering without losing raw statistics;
2. lemma and word-family analysis;
3. vocabulary coverage and section-by-section progression;
4. SQLite-backed multi-book library;
5. `NEW / SEEN / LEARNING / KNOWN / IGNORED` vocabulary states;
6. previewing a new book against personal vocabulary history;
7. phrases/collocations and example sentences;
8. flashcard export;
9. optional local browser dashboard.

The raw per-book analysis remains inspectable/exportable even after SQLite becomes the primary
library store.
