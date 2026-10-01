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


def test_analysis_builds_learning_candidates_with_configurable_threshold() -> None:
    book = Book(
        title="Learning",
        author=None,
        source_path="learning.epub",
        sections=(
            _section("c1", 1, "One", "brain brain brain memory memory the the"),
            _section("c2", 2, "Two", "brain memory"),
        ),
    )

    result = analyze_book(book, learning_min_count=3)

    assert result.learning_min_count == 3
    assert [stat.lemma for stat in result.learning_stats] == ["brain", "memory"]
    assert result.learning_stats[0].rank == 1
    assert result.learning_stats[0].section_count == 2


def test_analysis_rejects_invalid_learning_min_count() -> None:
    book = Book(
        title="Learning",
        author=None,
        source_path="learning.epub",
        sections=(_section("c1", 1, "One", "brain"),),
    )

    with pytest.raises(ValueError, match="learning_min_count"):
        analyze_book(book, learning_min_count=0)


def test_known_profile_filters_learning_candidates_and_tracks_coverage() -> None:
    book = Book(
        title="Known",
        author=None,
        source_path="known.epub",
        sections=(
            _section(
                "c1",
                1,
                "One",
                "The child child brain brain brain memory memory memory.",
            ),
        ),
    )

    result = analyze_book(
        book,
        learning_min_count=2,
        known_words={"children", "brain"},
    )

    assert result.known_profile_enabled
    assert result.known_profile_size == 2
    assert result.known_lemmas == frozenset({"child", "brain"})
    assert result.known_content_tokens == 5
    assert [stat.lemma for stat in result.learning_stats] == ["memory"]


def test_progression_tracks_new_repeated_and_cumulative_content_lemmas() -> None:
    book = Book(
        title="Progression",
        author=None,
        source_path="progression.epub",
        sections=(
            _section("c1", 1, "One", "brain child the"),
            _section("c2", 2, "Two", "brain child memory"),
            _section("c3", 3, "Three", "memory future"),
        ),
    )

    result = analyze_book(book)
    first, second, third = result.progression_stats

    assert first.content_lemmas == 2
    assert first.new_content_lemmas == 2
    assert first.repeated_content_lemmas == 0
    assert first.cumulative_content_lemmas == 2
    assert first.content_reuse_percentage == 0.0

    assert second.content_lemmas == 3
    assert second.new_content_lemmas == 1
    assert second.repeated_content_lemmas == 2
    assert second.cumulative_content_lemmas == 3
    assert second.content_reuse_percentage == pytest.approx(2 / 3 * 100)

    assert third.content_lemmas == 2
    assert third.new_content_lemmas == 1
    assert third.repeated_content_lemmas == 1
    assert third.cumulative_content_lemmas == 4
    assert third.content_reuse_percentage == 50.0


def test_progression_tracks_profile_unknown_vocabulary() -> None:
    book = Book(
        title="Progression",
        author=None,
        source_path="progression.epub",
        sections=(
            _section("c1", 1, "One", "brain child"),
            _section("c2", 2, "Two", "brain child memory"),
        ),
    )

    result = analyze_book(book, known_words={"brain"})
    first, second = result.progression_stats

    assert first.unknown_content_lemmas == 1
    assert first.new_unknown_content_lemmas == 1
    assert first.cumulative_unknown_content_lemmas == 1
    assert second.unknown_content_lemmas == 2
    assert second.new_unknown_content_lemmas == 1
    assert second.cumulative_unknown_content_lemmas == 2


def test_proper_nouns_are_kept_in_raw_stats_but_removed_from_learning_candidates() -> None:
    book = Book(
        title="Names",
        author=None,
        source_path="names.epub",
        sections=(
            _section(
                "c1",
                1,
                "One",
                "Tina helps children. The children talk to Tina. Tina knows Katie. "
                "Katie listens to Tina. Brain grows. The brain changes. brain brain.",
            ),
        ),
    )

    result = analyze_book(book, learning_min_count=2)
    by_lemma = {stat.lemma: stat for stat in result.lemma_stats}
    candidates = {stat.lemma for stat in result.learning_stats}

    assert by_lemma["tina"].is_proper_noun
    assert by_lemma["katie"].is_proper_noun
    assert not by_lemma["brain"].is_proper_noun
    assert "tina" not in candidates
    assert "katie" not in candidates
    assert "brain" in candidates


def test_capitalized_stopwords_are_not_marked_as_proper_nouns() -> None:
    book = Book(
        title="Pronoun",
        author=None,
        source_path="pronoun.epub",
        sections=(_section("c1", 1, "One", "I think I know. Tina knows me."),),
    )

    result = analyze_book(book, learning_min_count=1)
    by_lemma = {stat.lemma: stat for stat in result.lemma_stats}

    assert by_lemma["i"].is_stopword
    assert not by_lemma["i"].is_proper_noun
    assert by_lemma["tina"].is_proper_noun is False  # only one occurrence: conservative


def test_dialogue_initial_common_word_is_not_filtered_as_proper_noun() -> None:
    book = Book(
        title="Dialogue",
        author=None,
        source_path="dialogue.epub",
        sections=(
            _section(
                "c1",
                1,
                "One",
                'I called Tina. "Please listen," Tina said. '
                'I called Katie. "Please stay," Katie replied.',
            ),
        ),
    )

    result = analyze_book(book, learning_min_count=2)
    by_lemma = {stat.lemma: stat for stat in result.lemma_stats}

    assert by_lemma["tina"].is_proper_noun
    assert by_lemma["katie"].is_proper_noun
    assert not by_lemma["please"].is_proper_noun
