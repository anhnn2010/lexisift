"""Tests for vocabulary frequency analysis."""

import pytest

from lexisift.analysis import analyze_book
from lexisift.models import AnalysisScope, Book, Section, SectionKind



@pytest.fixture(autouse=True)
def _fake_dictionary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep frequency tests independent from the external morphology package."""

    def lookup(word: str) -> dict[str, tuple[str, ...]]:
        special = {
            "runs": {"VERB": ("run",)},
            "running": {"NOUN": ("running",), "VERB": ("run",)},
            "run": {"VERB": ("run",)},
            "strategies": {"NOUN": ("strategy",)},
            "strategy": {"NOUN": ("strategy",)},
        }
        return special.get(word, {"X": (word,)})

    monkeypatch.setattr("lexisift.analysis.lemmatizer._dictionary_lemmas", lookup)


def _section(
    section_id: str,
    order: int,
    title: str,
    text: str,
    kind: SectionKind = SectionKind.CHAPTER,
) -> Section:
    return Section(section_id, order, f"{section_id}.xhtml", title, text, kind)


def test_analyze_book_counts_frequency_section_spread_and_first_seen() -> None:
    book = Book(
        title="Example",
        author=None,
        source_path="example.epub",
        sections=(
            _section("c1", 1, "One", "Child brain child."),
            _section("c2", 2, "Two", "Brain grows."),
        ),
    )

    result = analyze_book(book)
    by_word = {stat.word: stat for stat in result.word_stats}

    assert result.total_tokens == 5
    assert result.unique_words == 3
    assert by_word["child"].count == 2
    assert by_word["child"].section_count == 1
    assert by_word["child"].first_seen_section == 1
    assert by_word["brain"].count == 2
    assert by_word["brain"].section_count == 2
    assert by_word["brain"].first_seen_section == 1


def test_main_scope_excludes_front_and_back_matter() -> None:
    book = Book(
        title="Example",
        author=None,
        source_path="example.epub",
        sections=(
            _section("toc", 1, "Contents", "chapter chapter", SectionKind.TOC),
            _section("intro", 2, "Introduction", "start here", SectionKind.INTRODUCTION),
            _section("c1", 3, "Chapter 1", "main words", SectionKind.CHAPTER),
            _section("ack", 4, "Acknowledgments", "thank you", SectionKind.ACKNOWLEDGMENTS),
        ),
    )

    result = analyze_book(book, scope=AnalysisScope.MAIN)
    by_word = {stat.word: stat for stat in result.word_stats}

    assert result.total_tokens == 4
    assert "chapter" not in by_word
    assert "thank" not in by_word
    assert by_word["start"].first_seen_section == 2
    assert [stat.included for stat in result.section_stats] == [False, True, True, False]


def test_analysis_marks_stopwords_and_builds_word_families() -> None:
    book = Book(
        title="Families",
        author=None,
        source_path="families.epub",
        sections=(
            _section(
                "c1",
                1,
                "One",
                "The child runs. Children are running with the child. Strategies strategy.",
            ),
        ),
    )

    result = analyze_book(book)
    by_word = {stat.word: stat for stat in result.word_stats}
    by_lemma = {stat.lemma: stat for stat in result.lemma_stats}

    assert by_word["the"].is_stopword
    assert not by_word["child"].is_stopword
    assert by_word["children"].lemma == "child"
    assert by_word["running"].lemma == "run"
    assert by_word["runs"].lemma == "run"
    assert by_word["strategies"].lemma == "strategy"
    assert by_lemma["child"].count == 3
    assert set(by_lemma["child"].forms) == {"child", "children"}
    assert by_lemma["run"].count == 2
    assert result.unique_lemmas < result.unique_words
    assert result.content_tokens < result.total_tokens


def test_coverage_reaches_one_hundred_percent() -> None:
    book = Book(
        title="Coverage",
        author=None,
        source_path="coverage.epub",
        sections=(_section("c1", 1, "One", "brain brain child"),),
    )

    result = analyze_book(book)

    assert result.coverage_stats[0].lemma == "brain"
    assert result.coverage_stats[0].cumulative_percentage == 2 / 3 * 100
    assert result.coverage_stats[-1].cumulative_percentage == 100.0
