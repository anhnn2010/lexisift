"""Tests for the built-in English stop-word set."""

from lexisift.analysis.stopwords import is_stopword


def test_common_function_words_and_contractions_are_stopwords() -> None:
    assert is_stopword("the")
    assert is_stopword("it's")
    assert is_stopword("don't")
    assert is_stopword("may")
    assert is_stopword("might")
    assert not is_stopword("brain")
