"""Book-level word frequency analysis."""

from __future__ import annotations

from collections import Counter, defaultdict

from lexisift.analysis.tokenizer import tokenize
from lexisift.models import AnalysisResult, Book, WordStat


def analyze_book(book: Book) -> AnalysisResult:
    """Count normalized words and chapter spread for a book."""

    counts: Counter[str] = Counter()
    chapter_ids_by_word: defaultdict[str, set[str]] = defaultdict(set)

    for chapter in book.chapters:
        tokens = tokenize(chapter.text)
        counts.update(tokens)
        for word in set(tokens):
            chapter_ids_by_word[word].add(chapter.chapter_id)

    total_tokens = sum(counts.values())
    stats = tuple(
        WordStat(
            word=word,
            count=count,
            chapter_count=len(chapter_ids_by_word[word]),
            percentage=(count / total_tokens * 100.0) if total_tokens else 0.0,
        )
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )

    return AnalysisResult(
        book=book,
        total_tokens=total_tokens,
        unique_words=len(counts),
        word_stats=stats,
    )
