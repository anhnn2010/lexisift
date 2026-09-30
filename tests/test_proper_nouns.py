"""Tests for conservative capitalization-based proper-noun detection."""

from lexisift.analysis.proper_nouns import is_likely_proper_noun


def test_repeated_mid_sentence_capitalization_is_likely_proper_noun() -> None:
    assert is_likely_proper_noun(
        total_count=10,
        capitalized_count=10,
        mid_sentence_capitalized_count=8,
    )


def test_sentence_initial_capitalization_alone_is_not_proper_noun() -> None:
    assert not is_likely_proper_noun(
        total_count=4,
        capitalized_count=4,
        mid_sentence_capitalized_count=0,
    )


def test_mixed_case_common_word_is_not_proper_noun() -> None:
    assert not is_likely_proper_noun(
        total_count=10,
        capitalized_count=3,
        mid_sentence_capitalized_count=2,
    )
