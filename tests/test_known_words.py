"""Tests for known-vocabulary profile loading and resolution."""

from pathlib import Path

import pytest

from lexisift.analysis.known_words import (
    KnownWordsError,
    load_known_words,
    resolve_known_lemmas,
)
from lexisift.models import LemmaStat


def _lemma(lemma: str, forms: tuple[str, ...]) -> LemmaStat:
    return LemmaStat(
        lemma=lemma,
        is_stopword=False,
        count=5,
        section_count=2,
        first_seen_section=1,
        percentage=1.0,
        forms=forms,
    )


def test_load_known_words_supports_comments_and_normalization(tmp_path: Path) -> None:
    source = tmp_path / "known_words.txt"
    source.write_text(
        "# Core vocabulary\nChild\nchildren  # same family\n\nWELL-BEING\n",
        encoding="utf-8",
    )

    assert load_known_words(source) == frozenset({"child", "children", "well-being"})


def test_load_known_words_rejects_multiword_entries(tmp_path: Path) -> None:
    source = tmp_path / "known_words.txt"
    source.write_text("whole brain\n", encoding="utf-8")

    with pytest.raises(KnownWordsError, match="exactly one word"):
        load_known_words(source)


def test_resolve_known_lemmas_accepts_observed_surface_forms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "lexisift.analysis.known_words.lemmatize_word",
        lambda word: "child" if word == "children" else word,
    )
    stats = (
        _lemma("child", ("child", "children", "children's")),
        _lemma("brain", ("brain", "brains")),
    )

    resolved = resolve_known_lemmas({"children"}, stats)

    assert resolved == frozenset({"child"})
