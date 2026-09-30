"""Unicode-aware word tokenization for book text."""

from __future__ import annotations

import re
import unicodedata

_WORD_RE = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*", flags=re.UNICODE)
_TRANSLATION = str.maketrans(
    {
        "’": "'",
        "‘": "'",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
    }
)


def normalize_text(text: str) -> str:
    """Normalize Unicode punctuation and composition before tokenization."""

    return unicodedata.normalize("NFC", text).translate(_TRANSLATION)


def tokenize(text: str) -> tuple[str, ...]:
    """Return normalized case-folded word tokens from text.

    Apostrophes and hyphens inside a word are preserved so forms such as
    ``don't`` and ``well-being`` remain single tokens.
    """

    normalized = normalize_text(text)
    return tuple(match.group(0).casefold() for match in _WORD_RE.finditer(normalized))
