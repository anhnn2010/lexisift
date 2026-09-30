"""Tests for conservative lexical-resource-backed English lemmatization."""

from unittest.mock import patch

from lexisift.analysis.lemmatizer import build_lemma_map, lemmatize_word


def _fake_lookup(word: str) -> dict[str, tuple[str, ...]]:
    data: dict[str, dict[str, tuple[str, ...]]] = {
        "run": {"NOUN": ("run",), "VERB": ("run",)},
        "runs": {"NOUN": ("run",), "VERB": ("run",)},
        "running": {"NOUN": ("running",), "VERB": ("run",)},
        "strategy": {"NOUN": ("strategy",)},
        "strategies": {"NOUN": ("strategy",)},
        "child": {"NOUN": ("child",)},
        "inner": {"ADJ": ("inner",)},
        "offer": {"NOUN": ("offer",), "VERB": ("offer",)},
        "even": {"ADJ": ("even",), "VERB": ("even",)},
        "evening": {"NOUN": ("evening",), "VERB": ("even",)},
        "letter": {"NOUN": ("letter",)},
        "news": {"NOUN": ("news",)},
        "dinner": {"NOUN": ("dinner",)},
        "think": {"VERB": ("think",)},
        "thinks": {"VERB": ("think",)},
        "thinking": {"NOUN": ("thinking",), "VERB": ("think",)},
        "develop": {"VERB": ("develop",)},
        "develops": {"VERB": ("develop",)},
        "developed": {"ADJ": ("developed",), "VERB": ("develop",)},
        "leave": {"VERB": ("leave",)},
        "leaving": {"VERB": ("leave",)},
        "leaves": {"NOUN": ("leaf",), "VERB": ("leave",)},
        "lives": {"NOUN": ("life",), "VERB": ("live",)},
        "left": {"VERB": ("leave",)},
        "see": {"VERB": ("see",)},
        "saw": {"VERB": ("see",), "NOUN": ("saw",)},
    }
    return data.get(word, {})


def test_lemma_map_groups_supported_regular_inflections() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        mapping = build_lemma_map(
            {"run", "runs", "running", "strategy", "strategies", "children"}
        )

    assert mapping["runs"] == "run"
    assert mapping["running"] == "run"
    assert mapping["strategies"] == "strategy"
    assert mapping["children"] == "child"


def test_lemma_map_keeps_ambiguous_evening_but_resolves_supported_thinking() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        mapping = build_lemma_map({"even", "evening", "think", "thinks", "thinking"})

    assert mapping["evening"] == "evening"
    assert mapping["thinking"] == "think"


def test_lemma_map_groups_regular_developed_when_supported() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        mapping = build_lemma_map({"develop", "develops", "developed"})

    assert mapping["developed"] == "develop"
    assert mapping["develops"] == "develop"


def test_lemma_map_does_not_guess_irregular_homographs_without_pos() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        mapping = build_lemma_map({"leave", "leaving", "leaves", "left", "see", "saw"})

    assert mapping["leaving"] == "leave"
    assert mapping["leaves"] == "leaves"
    assert mapping["left"] == "left"
    assert mapping["saw"] == "saw"


def test_lemmatizer_preserves_common_contractions() -> None:
    assert lemmatize_word("it's") == "it's"
    assert lemmatize_word("that's") == "that's"
    assert lemmatize_word("don't") == "don't"


def test_lemmatizer_handles_possessives_and_safe_irregulars() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        assert lemmatize_word("child's") == "child"
        assert lemmatize_word("children's") == "child"

    assert lemmatize_word("children") == "child"
    assert lemmatize_word("better") == "good"
    assert lemmatize_word("went") == "go"
    assert lemmatize_word("gone") == "go"


def test_lemmatizer_keeps_dictionary_lemmas_unchanged() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        assert lemmatize_word("inner") == "inner"
        assert lemmatize_word("offer") == "offer"
        assert lemmatize_word("letter") == "letter"
        assert lemmatize_word("news") == "news"
        assert lemmatize_word("dinner") == "dinner"


def test_lemmatizer_keeps_multi_lemma_surface_unchanged_without_pos() -> None:
    with patch("lexisift.analysis.lemmatizer._dictionary_lemmas", side_effect=_fake_lookup):
        mapping = build_lemma_map({"live", "lives"})

    assert mapping["lives"] == "lives"
