"""Unicode-aware word tokenization for book text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

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
_SENTENCE_END = frozenset(".!?")
_QUOTE_OR_BRACKET = frozenset("\"'“”‘’([{<")


@dataclass(frozen=True, slots=True)
class TokenObservation:
    """One token plus the casing evidence needed for proper-noun heuristics."""

    word: str
    surface: str
    sentence_initial: bool

    @property
    def is_capitalized(self) -> bool:
        """Return whether the token starts with an uppercase letter."""

        return bool(self.surface) and self.surface[0].isupper()


def normalize_text(text: str) -> str:
    """Normalize Unicode punctuation and composition before tokenization."""

    return unicodedata.normalize("NFC", text).translate(_TRANSLATION)


def _split_long_hyphen_chain(token: str) -> tuple[str, ...]:
    """Split stylistic sentence-like hyphen chains while keeping normal compounds."""

    parts = token.split("-")
    if len(parts) > _MAX_HYPHEN_PARTS:
        return tuple(part for part in parts if part)
    return (token,)


def _is_sentence_initial(text: str, start: int) -> bool:
    """Return whether a token starts the text or follows sentence-ending punctuation."""

    index = start - 1
    while index >= 0 and text[index].isspace():
        index -= 1
    while index >= 0 and text[index] in _QUOTE_OR_BRACKET:
        index -= 1
    return index < 0 or text[index] in _SENTENCE_END


def observe_tokens(text: str) -> tuple[TokenObservation, ...]:
    """Return normalized tokens while preserving capitalization context.

    The normalized ``word`` is identical to the output of :func:`tokenize`, while
    ``surface`` preserves the original letter casing after Unicode punctuation
    normalization. ``sentence_initial`` lets downstream analysis avoid mistaking
    ordinary sentence-initial capitalization for a proper noun.
    """

    normalized = normalize_text(text)
    observations: list[TokenObservation] = []
    for match in _WORD_RE.finditer(normalized):
        surface = match.group(0)
        sentence_initial = _is_sentence_initial(normalized, match.start())
        parts = _split_long_hyphen_chain(surface)
        for index, part in enumerate(parts):
            observations.append(
                TokenObservation(
                    word=part.casefold(),
                    surface=part,
                    sentence_initial=sentence_initial if index == 0 else False,
                )
            )
    return tuple(observations)


def tokenize(text: str) -> tuple[str, ...]:
    """Return normalized case-folded word tokens from text.

    Apostrophes and lexical hyphens inside a word are preserved so forms such as
    ``don't``, ``well-being``, and ``four-year-old`` remain single tokens. En/em
    dashes are treated as separators. Very long hyphen chains are split because
    they are typically stylistic phrases rather than useful vocabulary entries.
    """

    return tuple(observation.word for observation in observe_tokens(text))
