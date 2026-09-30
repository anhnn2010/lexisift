"""Tests for vocabulary frequency analysis."""

from lexisift.analysis import analyze_book
from lexisift.models import AnalysisScope, Book, Section, SectionKind


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
