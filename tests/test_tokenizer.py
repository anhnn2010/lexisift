"""Tests for LexiSift word tokenization."""

from lexisift.analysis.tokenizer import tokenize


def test_tokenize_preserves_internal_apostrophes_and_lexical_hyphens() -> None:
    text = "Children don't lose well-being ‑ four-year-old kids are learning."

    assert tokenize(text) == (
        "children",
        "don't",
        "lose",
        "well-being",
        "four-year-old",
        "kids",
        "are",
        "learning",
    )


def test_tokenize_treats_dashes_as_word_separators() -> None:
    text = "brain—and world–or you—to"

    assert tokenize(text) == ("brain", "and", "world", "or", "you", "to")


def test_tokenize_splits_stylistic_long_hyphen_chains() -> None:
    text = "bribe-the-toddler-into-the-car-seat-so-we-can-rush"

    assert tokenize(text) == (
        "bribe",
        "the",
        "toddler",
        "into",
        "the",
        "car",
        "seat",
        "so",
        "we",
        "can",
        "rush",
    )


def test_tokenize_casefolds_unicode_words() -> None:
    assert tokenize("CAFÉ café") == ("café", "café")
