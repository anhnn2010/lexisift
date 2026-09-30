"""Book-level word, lemma, and coverage analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Collection

from lexisift.analysis.known_words import resolve_known_lemmas
from lexisift.analysis.learning import build_learning_stats
from lexisift.analysis.lemmatizer import build_lemma_map
from lexisift.analysis.stopwords import is_stopword
from lexisift.analysis.tokenizer import tokenize
from lexisift.models import (
    AnalysisResult,
    AnalysisScope,
    Book,
    CoverageStat,
    LemmaStat,
    SectionStat,
    WordStat,
)


class AnalysisError(ValueError):
    """Raised when the selected analysis scope cannot be analyzed."""


def analyze_book(
    book: Book,
    scope: AnalysisScope = AnalysisScope.ALL,
    learning_min_count: int = 3,
    known_words: Collection[str] | None = None,
) -> AnalysisResult:
    """Analyze words, word families, coverage, and learning candidates."""

    if learning_min_count < 1:
        raise AnalysisError("learning_min_count must be at least 1")

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
    vocabulary = frozenset(counts)
    lemma_by_word = build_lemma_map(vocabulary)

    word_stats = tuple(
        WordStat(
            word=word,
            lemma=lemma_by_word[word],
            is_stopword=is_stopword(word) or is_stopword(lemma_by_word[word]),
            count=count,
            section_count=len(section_ids_by_word[word]),
            first_seen_section=first_seen_by_word[word],
            percentage=(count / total_tokens * 100.0) if total_tokens else 0.0,
        )
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )

    lemma_counts: Counter[str] = Counter()
    section_ids_by_lemma: defaultdict[str, set[str]] = defaultdict(set)
    first_seen_by_lemma: dict[str, int] = {}
    forms_by_lemma: defaultdict[str, set[str]] = defaultdict(set)

    for section, tokens in included:
        section_lemmas: set[str] = set()
        for word in tokens:
            lemma = lemma_by_word[word]
            lemma_counts[lemma] += 1
            forms_by_lemma[lemma].add(word)
            section_lemmas.add(lemma)
        for lemma in section_lemmas:
            section_ids_by_lemma[lemma].add(section.section_id)
            first_seen_by_lemma.setdefault(lemma, section.order)

    lemma_stats = tuple(
        LemmaStat(
            lemma=lemma,
            is_stopword=is_stopword(lemma),
            count=count,
            section_count=len(section_ids_by_lemma[lemma]),
            first_seen_section=first_seen_by_lemma[lemma],
            percentage=(count / total_tokens * 100.0) if total_tokens else 0.0,
            forms=tuple(
                sorted(forms_by_lemma[lemma], key=lambda form: (-counts[form], form))
            ),
        )
        for lemma, count in sorted(lemma_counts.items(), key=lambda item: (-item[1], item[0]))
    )

    coverage_rows: list[CoverageStat] = []
    cumulative_count = 0
    for rank, stat in enumerate(lemma_stats, start=1):
        cumulative_count += stat.count
        coverage_rows.append(
            CoverageStat(
                rank=rank,
                lemma=stat.lemma,
                count=stat.count,
                cumulative_count=cumulative_count,
                cumulative_percentage=(cumulative_count / total_tokens * 100.0)
                if total_tokens
                else 0.0,
            )
        )

    content_tokens = sum(stat.count for stat in word_stats if not stat.is_stopword)
    unique_content_words = sum(1 for stat in word_stats if not stat.is_stopword)
    unique_content_lemmas = sum(1 for stat in lemma_stats if not stat.is_stopword)
    analyzed_sections = sum(1 for stat in section_stats if stat.included)
    known_profile_enabled = known_words is not None
    known_profile = frozenset(known_words or ())
    known_lemmas = resolve_known_lemmas(known_profile, lemma_stats)
    known_content_tokens = sum(
        stat.count
        for stat in lemma_stats
        if not stat.is_stopword and stat.lemma in known_lemmas
    )
    learning_stats = build_learning_stats(
        lemma_stats,
        analyzed_sections=analyzed_sections,
        min_count=learning_min_count,
        excluded_lemmas=known_lemmas,
    )

    return AnalysisResult(
        book=book,
        scope=scope,
        total_tokens=total_tokens,
        content_tokens=content_tokens,
        unique_words=len(counts),
        unique_content_words=unique_content_words,
        unique_lemmas=len(lemma_counts),
        unique_content_lemmas=unique_content_lemmas,
        learning_min_count=learning_min_count,
        known_profile_enabled=known_profile_enabled,
        known_profile_size=len(known_profile),
        known_lemmas=known_lemmas,
        known_content_tokens=known_content_tokens,
        section_stats=section_stats,
        word_stats=word_stats,
        lemma_stats=lemma_stats,
        coverage_stats=tuple(coverage_rows),
        learning_stats=learning_stats,
    )
