"""Tests for book-local learning candidate ranking."""

from lexisift.analysis.learning import build_learning_stats
from lexisift.models import LemmaStat


def _lemma(
    lemma: str,
    count: int,
    section_count: int,
    *,
    stopword: bool = False,
) -> LemmaStat:
    return LemmaStat(
        lemma=lemma,
        is_stopword=stopword,
        count=count,
        section_count=section_count,
        first_seen_section=1,
        percentage=float(count),
        forms=(lemma,),
    )


def test_learning_candidates_filter_stopwords_and_low_frequency() -> None:
    stats = (
        _lemma("brain", 10, 4),
        _lemma("rare", 2, 2),
        _lemma("the", 30, 4, stopword=True),
    )

    result = build_learning_stats(stats, analyzed_sections=4, min_count=3)

    assert [stat.lemma for stat in result] == ["brain"]


def test_learning_candidates_reward_section_spread() -> None:
    stats = (
        _lemma("broad", 10, 4),
        _lemma("local", 10, 1),
    )

    result = build_learning_stats(stats, analyzed_sections=4, min_count=1)

    assert [stat.lemma for stat in result] == ["broad", "local"]
    assert result[0].priority_score == 20.0
    assert result[1].priority_score == 12.5
    assert result[0].section_coverage_percentage == 100.0
    assert result[1].section_coverage_percentage == 25.0
