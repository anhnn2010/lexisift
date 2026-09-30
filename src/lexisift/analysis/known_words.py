"""Load and resolve a user's known-vocabulary profile."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from pathlib import Path

from lexisift.analysis.lemmatizer import lemmatize_word
from lexisift.analysis.tokenizer import tokenize
from lexisift.models import LemmaStat


class KnownWordsError(ValueError):
    """Raised when a known-vocabulary file cannot be parsed."""


def load_known_words(path: str | Path) -> frozenset[str]:
    """Load normalized vocabulary entries from a UTF-8 text file.

    The format is intentionally human-editable: one word or lemma per line.
    Blank lines and lines beginning with ``#`` are ignored. Inline comments are
    also allowed after whitespace followed by ``#``.
    """

    source = Path(path).expanduser()
    try:
        text = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise KnownWordsError(f"Could not read known words file: {source}: {exc}") from exc

    entries: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Keep apostrophes inside tokens while allowing a readable inline note:
        # ``children  # family: child``.
        candidate = stripped.split(" #", maxsplit=1)[0].strip()
        tokens = tokenize(candidate)
        if len(tokens) != 1:
            raise KnownWordsError(
                f"Known words line {line_number} must contain exactly one word or lemma: "
                f"{raw_line!r}"
            )
        entries.add(tokens[0])

    return frozenset(entries)


def resolve_known_lemmas(
    known_words: Collection[str],
    lemma_stats: Sequence[LemmaStat],
) -> frozenset[str]:
    """Resolve profile entries to lemma families observed in the current book.

    A profile entry can be either a lemma (``child``) or an observed surface
    form (``children``). Independent lemmatization is deliberately conservative,
    matching LexiSift's normal morphology policy.
    """

    if not known_words:
        return frozenset()

    normalized = frozenset(word.casefold() for word in known_words)
    canonical = frozenset(lemmatize_word(word) for word in normalized)
    keys = normalized | canonical

    resolved: set[str] = set()
    for stat in lemma_stats:
        if stat.lemma in keys or any(form in normalized for form in stat.forms):
            resolved.add(stat.lemma)
    return frozenset(resolved)
