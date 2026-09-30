"""Tests for generated report files."""

from pathlib import Path

import pytest

from lexisift.analysis import analyze_book
from lexisift.models import Book, Section, SectionKind
from lexisift.reporting import write_reports


@pytest.fixture(autouse=True)
def _fake_dictionary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep report tests independent from the external morphology package."""

    monkeypatch.setattr(
        "lexisift.analysis.lemmatizer._dictionary_lemmas",
        lambda word: {"X": (word,)},
    )


def test_reports_include_progression_csv(tmp_path: Path) -> None:
    book = Book(
        title="Reports",
        author=None,
        source_path="reports.epub",
        sections=(
            Section("c1", 1, "c1.xhtml", "One", "brain child", SectionKind.CHAPTER),
            Section("c2", 2, "c2.xhtml", "Two", "brain memory", SectionKind.CHAPTER),
        ),
    )
    result = analyze_book(book, known_words={"brain"})

    destination = write_reports(result, tmp_path / "out")
    progression = (destination / "progression.csv").read_text(encoding="utf-8")
    summary = (destination / "summary.txt").read_text(encoding="utf-8")

    assert "new_content_lemmas" in progression
    assert "new_unknown_content_lemmas" in progression
    assert "Vocabulary progression:" in summary
    assert "Book-new unknown content lemmas: 2" in summary


def test_reports_include_proper_noun_audit_file(tmp_path: Path) -> None:
    book = Book(
        title="Names",
        author=None,
        source_path="names.epub",
        sections=(
            Section(
                "c1",
                1,
                "c1.xhtml",
                "One",
                "Tina talks to Katie. Katie talks to Tina. Tina smiles.",
                SectionKind.CHAPTER,
            ),
        ),
    )
    result = analyze_book(book, learning_min_count=1)

    destination = write_reports(result, tmp_path / "out")
    proper_nouns = (destination / "proper_nouns.csv").read_text(encoding="utf-8")
    learning = (destination / "learning_words.csv").read_text(encoding="utf-8")

    assert "tina" in proper_nouns
    assert "katie" in proper_nouns
    assert "tina" not in learning
    assert "katie" not in learning
