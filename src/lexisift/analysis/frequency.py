"""Book-level word frequency analysis."""

from __future__ import annotations

from collections import Counter, defaultdict

from lexisift.analysis.tokenizer import tokenize
from lexisift.models import (
    AnalysisResult,
    AnalysisScope,
    Book,
    SectionStat,
    WordStat,
)


class AnalysisError(ValueError):
    """Raised when the selected analysis scope cannot be analyzed."""


def analyze_book(
    book: Book,
    scope: AnalysisScope = AnalysisScope.ALL,
) -> AnalysisResult:
    """Count normalized words and section spread for a book."""

    tokenized_sections = [(section, tokenize(section.text)) for section in book.sections]
    section_stats = tuple(
        SectionStat(
            section_id=section.section_id,
            order=section.order,
            title=section.title,
            kind=section.kind,
            token_count=len(tokens),
            included=scope is AnalysisScope.ALL or section.is_main_content,
        )
        for section, tokens in tokenized_sections
    )

    included = [
        (section, tokens)
        for section, tokens in tokenized_sections
        if scope is AnalysisScope.ALL or section.is_main_content
    ]
    if not included:
        raise AnalysisError(f"No sections are available for analysis scope: {scope.value}")

    counts: Counter[str] = Counter()
    section_ids_by_word: defaultdict[str, set[str]] = defaultdict(set)
    first_seen_by_word: dict[str, int] = {}

    for section, tokens in included:
        counts.update(tokens)
        for word in set(tokens):
            section_ids_by_word[word].add(section.section_id)
            first_seen_by_word.setdefault(word, section.order)

    total_tokens = sum(counts.values())
    stats = tuple(
        WordStat(
            word=word,
            count=count,
            section_count=len(section_ids_by_word[word]),
            first_seen_section=first_seen_by_word[word],
            percentage=(count / total_tokens * 100.0) if total_tokens else 0.0,
        )
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )

    return AnalysisResult(
        book=book,
        scope=scope,
        total_tokens=total_tokens,
        unique_words=len(counts),
        section_stats=section_stats,
        word_stats=stats,
    )
