"""Unicode-aware word tokenization for book text."""

from __future__ import annotations

import re
import unicodedata

_WORD_RE = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*", flags=re.UNICODE)
_MAX_HYPHEN_PARTS = 4
_TRANSLATION = str.maketrans(
    {
        "’": "'",
        "‘": "'",
        # True hyphen characters remain internal word punctuation.
        "‐": "-",
        "‑": "-",
        # Dash characters act as separators, not as lexical hyphens.
        "‒": " ",
        "–": " ",
        "—": " ",
        "―": " ",
    }
)


def normalize_text(text: str) -> str:
    """Normalize Unicode punctuation and composition before tokenization."""

    return unicodedata.normalize("NFC", text).translate(_TRANSLATION)


def _split_long_hyphen_chain(token: str) -> tuple[str, ...]:
    """Split stylistic sentence-like hyphen chains while keeping normal compounds."""

    parts = token.split("-")
    if len(parts) > _MAX_HYPHEN_PARTS:
        return tuple(part for part in parts if part)
    return (token,)


def tokenize(text: str) -> tuple[str, ...]:
    """Return normalized case-folded word tokens from text.

    Apostrophes and lexical hyphens inside a word are preserved so forms such as
    ``don't``, ``well-being``, and ``four-year-old`` remain single tokens. En/em
    dashes are treated as separators. Very long hyphen chains are split because
    they are typically stylistic phrases rather than useful vocabulary entries.
    """

    normalized = normalize_text(text)
    tokens: list[str] = []
    for match in _WORD_RE.finditer(normalized):
        token = match.group(0).casefold()
        tokens.extend(_split_long_hyphen_chain(token))
    return tuple(tokens)
