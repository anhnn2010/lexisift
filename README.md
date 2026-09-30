# LexiSift

**Understand the vocabulary behind a book.**

LexiSift is a local, offline-first Python CLI for analyzing vocabulary in EPUB books. It follows the EPUB spine, classifies readable sections, tokenizes English text, groups conservative word families, separates common stop words, reports cumulative reading coverage, ranks repeated learning candidates, and can filter those candidates against a personal known-vocabulary profile.

## Current version

`0.4.0`

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

## Known vocabulary profile

Create a UTF-8 text file with one known word or lemma per line:

```text
# known_words.txt
child
brain
family
understand
children  # surface forms are accepted too
```

Blank lines and comments are ignored. Analyze a book against the profile:

```bash
lexisift analyze book.epub \
  --scope main \
  --known-words known_words.txt \
  -o output/book
```

The profile is matched against lemma families. For example, an entry such as `children` can mark the `child` family as known. LexiSift remains conservative for ambiguous morphology rather than guessing a part of speech.

With a known-word profile, `learning_words.csv` automatically excludes known families and LexiSift additionally writes `known_words.csv` and `unknown_words.csv`.

## Reports

LexiSift always writes:

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

When `--known-words` is provided, it also writes:

```text
├── known_words.csv
└── unknown_words.csv
```

### `sections.csv`

EPUB spine order, semantic section classification, inclusion state, and token counts.

### `vocabulary.csv`

Every normalized surface form with:

- `word`
- `lemma`
- `is_stopword`
- `is_known`
- `count`
- `section_count`
- `first_seen_section`
- `percentage`

`is_known` is blank when no known-vocabulary profile is supplied.

### `content_words.csv`

Surface-word statistics with common English stop words removed. It also contains `is_known` when a profile is active.

### `lemmas.csv`

Dictionary-form word-family aggregation, including observed forms and known state. For example:

```text
child    <- child | children
run      <- run | runs | running
strategy <- strategy | strategies
```

LexiSift uses LemmInflect's packaged English lexical resources rather than suffix stemming. It prefers correctness over aggressive grouping: automatic dictionary grouping is limited to conservative regular inflections, while irregular forms are folded only through a small curated safe list. Ambiguous homographs such as `left`/`leave` and `saw`/`see` remain separate without contextual POS evidence. Dictionary-ambiguous regular forms remain unchanged unless an independent form in the same book supports one family. Lexical possessives such as `child's` are folded into their base word, while common apostrophe contractions remain intact.

### `known_words.csv`

Content lemma families from the current book that match the supplied known-vocabulary profile. This file is written only when `--known-words` is used.

### `unknown_words.csv`

Every content lemma family in the current book that is not covered by the supplied known-vocabulary profile, regardless of frequency. This is the complete unknown-vocabulary view before learning-priority filtering.

### `learning_words.csv`

A book-local candidate list intended for vocabulary review. It is grouped by lemma, excludes stop words and known lemmas, and by default removes lemmas that occur fewer than 3 times. Columns include:

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

Frequency remains the main signal, while vocabulary that recurs across more of the book receives a modest bonus. This is a book-local learning priority, not a general English difficulty score.

### `coverage.csv`

Lemmas ranked by frequency with cumulative token coverage. This answers questions such as how much of the running text is covered by the 100, 500, 1000, or 2000 most frequent lemmas in the book.

### Known-vocabulary coverage in `summary.txt`

When a profile is active, the summary adds:

- profile entry count
- known content lemmas found in the book
- unknown content lemmas found in the book
- **known content-token coverage**: share of content-word tokens covered by known lemma families
- **estimated reading-token coverage**: stop-word tokens plus known content-word tokens as a share of all analyzed tokens

The estimated reading-token metric assumes common stop words are already readable; it is a transparent coverage estimate, not a claim about comprehension.

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

- persistent known / learning / new vocabulary state
- vocabulary progression by section/book
- multi-book SQLite library
- personalized reading coverage across books
- phrase and collocation analysis
- example sentence selection
- flashcard export
- KOReader reading-history integration
