"""Section-by-section vocabulary progression analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from lexisift.analysis.stopwords import is_stopword
from lexisift.models import Section, SectionProgressStat


def build_progression_stats(
    tokenized_sections: Sequence[tuple[Section, Sequence[str]]],
    lemma_by_word: Mapping[str, str],
    *,
    known_lemmas: frozenset[str] = frozenset(),
    known_profile_enabled: bool = False,
) -> tuple[SectionProgressStat, ...]:
    """Build cumulative vocabulary-growth statistics in reading order.

    A lemma is considered *new* only in the first analyzed section in which it
    appears. Content metrics exclude stop-word lemmas. When a known-vocabulary
    profile is active, profile-aware columns distinguish book-new vocabulary
    from vocabulary that is also unknown to the reader.
    """

    seen_lemmas: set[str] = set()
    seen_content_lemmas: set[str] = set()
    seen_unknown_content_lemmas: set[str] = set()
    rows: list[SectionProgressStat] = []

    for section, tokens in tokenized_sections:
        lemmas = {lemma_by_word[word] for word in tokens}
        content_lemmas = {lemma for lemma in lemmas if not is_stopword(lemma)}
        new_lemmas = lemmas - seen_lemmas
        new_content_lemmas = content_lemmas - seen_content_lemmas
        repeated_content_lemmas = content_lemmas & seen_content_lemmas
        content_token_count = sum(
            1
            for word in tokens
            if not (is_stopword(word) or is_stopword(lemma_by_word[word]))
        )
        content_reuse_percentage = (
            len(repeated_content_lemmas) / len(content_lemmas) * 100.0
            if content_lemmas
            else 0.0
        )

        seen_lemmas.update(lemmas)
        seen_content_lemmas.update(content_lemmas)

        if known_profile_enabled:
            unknown_content_lemmas = content_lemmas - known_lemmas
            new_unknown_content_lemmas = new_content_lemmas - known_lemmas
            seen_unknown_content_lemmas.update(unknown_content_lemmas)
            unknown_count: int | None = len(unknown_content_lemmas)
            new_unknown_count: int | None = len(new_unknown_content_lemmas)
            cumulative_unknown_count: int | None = len(seen_unknown_content_lemmas)
        else:
            unknown_count = None
            new_unknown_count = None
            cumulative_unknown_count = None

        rows.append(
            SectionProgressStat(
                section_id=section.section_id,
                order=section.order,
                title=section.title,
                kind=section.kind,
                token_count=len(tokens),
                content_token_count=content_token_count,
                unique_lemmas=len(lemmas),
                content_lemmas=len(content_lemmas),
                new_lemmas=len(new_lemmas),
                new_content_lemmas=len(new_content_lemmas),
                repeated_content_lemmas=len(repeated_content_lemmas),
                content_reuse_percentage=content_reuse_percentage,
                cumulative_lemmas=len(seen_lemmas),
                cumulative_content_lemmas=len(seen_content_lemmas),
                unknown_content_lemmas=unknown_count,
                new_unknown_content_lemmas=new_unknown_count,
                cumulative_unknown_content_lemmas=cumulative_unknown_count,
            )
        )

    return tuple(rows)
