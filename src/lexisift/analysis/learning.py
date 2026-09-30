"""Rank repeated content lemmas as transparent learning candidates."""

from __future__ import annotations

from collections.abc import Collection, Sequence

from lexisift.models import LearningWordStat, LemmaStat


def build_learning_stats(
    lemma_stats: Sequence[LemmaStat],
    *,
    analyzed_sections: int,
    min_count: int = 3,
    excluded_lemmas: Collection[str] = (),
) -> tuple[LearningWordStat, ...]:
    """Return ranked learning candidates from content lemmas.

    This is deliberately a book-local heuristic, not a claim about language
    difficulty. Stop words, known lemmas, and low-frequency lemmas are removed. Remaining
    lemmas receive a modest bonus for appearing across more analyzed sections,
    while raw book frequency remains the dominant signal.
    """

    if min_count < 1:
        raise ValueError("learning min count must be at least 1")
    if analyzed_sections < 1:
        return ()

    candidates: list[tuple[float, LemmaStat]] = []
    for stat in lemma_stats:
        if stat.is_stopword or stat.count < min_count or stat.lemma in excluded_lemmas:
            continue
        section_ratio = stat.section_count / analyzed_sections
        priority_score = stat.count * (1.0 + section_ratio)
        candidates.append((priority_score, stat))

    candidates.sort(
        key=lambda item: (
            -item[0],
            -item[1].count,
            -item[1].section_count,
            item[1].lemma,
        )
    )

    return tuple(
        LearningWordStat(
            rank=rank,
            lemma=stat.lemma,
            count=stat.count,
            section_count=stat.section_count,
            section_coverage_percentage=stat.section_count / analyzed_sections * 100.0,
            first_seen_section=stat.first_seen_section,
            book_percentage=stat.percentage,
            priority_score=priority_score,
            forms=stat.forms,
        )
        for rank, (priority_score, stat) in enumerate(candidates, start=1)
    )
