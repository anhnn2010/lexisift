"""Core data models used by LexiSift."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chapter:
    """One readable document in EPUB spine order."""

    chapter_id: str
    order: int
    href: str
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class Book:
    """An EPUB book and its ordered readable chapters."""

    title: str
    author: str | None
    source_path: str
    chapters: tuple[Chapter, ...]


@dataclass(frozen=True, slots=True)
class WordStat:
    """Frequency statistics for one normalized word."""

    word: str
    count: int
    chapter_count: int
    percentage: float


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Vocabulary analysis result for one book."""

    book: Book
    total_tokens: int
    unique_words: int
    word_stats: tuple[WordStat, ...]
