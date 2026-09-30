"""Conservative proper-noun detection from book-local capitalization evidence."""

from __future__ import annotations


_MIN_CAPITALIZED_RATIO = 0.80


def is_likely_proper_noun(
    *,
    total_count: int,
    capitalized_count: int,
    mid_sentence_capitalized_count: int,
) -> bool:
    """Return whether capitalization strongly suggests a proper noun.

    LexiSift deliberately avoids a language model here. A candidate must be
    capitalized in at least 80% of its observed occurrences and must appear
    capitalized away from sentence-initial position at least once. This keeps
    ordinary words that happen to begin sentences from disappearing from the
    learning list while filtering repeated names such as ``Tina`` or ``Katie``.
    """

    if total_count < 2 or capitalized_count < 2:
        return False
    if mid_sentence_capitalized_count < 1:
        return False
    return capitalized_count / total_count >= _MIN_CAPITALIZED_RATIO
