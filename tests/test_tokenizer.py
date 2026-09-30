"""Tests for LexiSift word tokenization."""

from lexisift.analysis.tokenizer import tokenize


def test_tokenize_preserves_internal_apostrophes_and_hyphens() -> None:
    text = "Children don't lose well-being — they’re learning."

    assert tokenize(text) == (
        "children",
        "don't",
        "lose",
        "well-being",
        "they're",
        "learning",
    )


def test_tokenize_casefolds_unicode_words() -> None:
    assert tokenize("CAFÉ café") == ("café", "café")
