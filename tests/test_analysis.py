"""Tests for vocabulary frequency analysis."""

from lexisift.analysis import analyze_book
from lexisift.models import Book, Chapter


def test_analyze_book_counts_frequency_and_chapter_spread() -> None:
    book = Book(
        title="Example",
        author=None,
        source_path="example.epub",
        chapters=(
            Chapter("c1", 1, "c1.xhtml", "One", "Child brain child."),
            Chapter("c2", 2, "c2.xhtml", "Two", "Brain grows."),
        ),
    )

    result = analyze_book(book)
    by_word = {stat.word: stat for stat in result.word_stats}

    assert result.total_tokens == 5
    assert result.unique_words == 3
    assert by_word["child"].count == 2
    assert by_word["child"].chapter_count == 1
    assert by_word["brain"].count == 2
    assert by_word["brain"].chapter_count == 2
