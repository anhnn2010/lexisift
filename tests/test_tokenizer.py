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


def test_observe_tokens_preserves_capitalization_and_sentence_position() -> None:
    from lexisift.analysis.tokenizer import observe_tokens

    observations = observe_tokens('Tina talks to Katie. Brain grows. The brain adapts.')
    by_surface = [(item.surface, item.word, item.sentence_initial) for item in observations]

    assert by_surface[0] == ("Tina", "tina", True)
    assert ("Katie", "katie", False) in by_surface
    brain_rows = [row for row in by_surface if row[1] == "brain"]
    assert brain_rows == [("Brain", "brain", True), ("brain", "brain", False)]


def test_observe_tokens_treats_newline_as_sentence_boundary() -> None:
    from lexisift.analysis.tokenizer import observe_tokens

    observations = observe_tokens("Previous text without punctuation\nPlease read this")
    please = next(item for item in observations if item.word == "please")

    assert please.sentence_initial


def test_observe_tokens_treats_opening_quote_as_sentence_boundary() -> None:
    from lexisift.analysis.tokenizer import observe_tokens

    observations = observe_tokens('He said, "Please sit here." Tina answered.')
    please = next(item for item in observations if item.word == "please")
    tina = next(item for item in observations if item.word == "tina")

    assert please.sentence_initial
    assert tina.sentence_initial
