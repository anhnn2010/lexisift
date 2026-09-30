"""Core data models used by LexiSift."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SectionKind(str, Enum):
    """Semantic category assigned to one EPUB spine document."""

    TITLE_PAGE = "title_page"
    COPYRIGHT = "copyright"
    DEDICATION = "dedication"
    TOC = "toc"
    FRONTMATTER = "frontmatter"
    INTRODUCTION = "introduction"
    CHAPTER = "chapter"
    CONCLUSION = "conclusion"
    APPENDIX = "appendix"
    ACKNOWLEDGMENTS = "acknowledgments"
    ABOUT_AUTHOR = "about_author"
    BACKMATTER = "backmatter"
    OTHER = "other"


_MAIN_CONTENT_KINDS = frozenset(
    {
        SectionKind.INTRODUCTION,
        SectionKind.CHAPTER,
        SectionKind.CONCLUSION,
    }
)


@dataclass(frozen=True, slots=True)
class Section:
    """One readable EPUB document in declared spine order."""

    section_id: str
    order: int
    href: str
    title: str
    text: str
    kind: SectionKind
    semantics: frozenset[str] = frozenset()

    @property
    def is_main_content(self) -> bool:
        """Return whether this section belongs to the main reading content."""

        return self.kind in _MAIN_CONTENT_KINDS


@dataclass(frozen=True, slots=True)
class Book:
    """An EPUB book and its ordered readable sections."""

    title: str
    author: str | None
    source_path: str
    sections: tuple[Section, ...]


class AnalysisScope(str, Enum):
    """Which EPUB sections contribute to vocabulary statistics."""

    ALL = "all"
    MAIN = "main"


@dataclass(frozen=True, slots=True)
class SectionStat:
    """Analysis metadata for one EPUB section."""

    section_id: str
    order: int
    title: str
    kind: SectionKind
    token_count: int
    included: bool


@dataclass(frozen=True, slots=True)
class WordStat:
    """Frequency statistics for one normalized surface word."""

    word: str
    lemma: str
    is_stopword: bool
    count: int
    section_count: int
    first_seen_section: int
    percentage: float
    capitalized_count: int = 0
    mid_sentence_capitalized_count: int = 0
    is_proper_noun: bool = False


@dataclass(frozen=True, slots=True)
class LemmaStat:
    """Aggregated statistics for one conservative word-family canonical form."""

    lemma: str
    is_stopword: bool
    count: int
    section_count: int
    first_seen_section: int
    percentage: float
    forms: tuple[str, ...]
    capitalized_count: int = 0
    mid_sentence_capitalized_count: int = 0
    is_proper_noun: bool = False


@dataclass(frozen=True, slots=True)
class CoverageStat:
    """Cumulative token coverage after including one ranked lemma."""

    rank: int
    lemma: str
    count: int
    cumulative_count: int
    cumulative_percentage: float


@dataclass(frozen=True, slots=True)
class LearningWordStat:
    """One book-local vocabulary candidate ranked for repeated exposure."""

    rank: int
    lemma: str
    count: int
    section_count: int
    section_coverage_percentage: float
    first_seen_section: int
    book_percentage: float
    priority_score: float
    forms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SectionProgressStat:
    """Vocabulary growth and reuse metrics for one analyzed section."""

    section_id: str
    order: int
    title: str
    kind: SectionKind
    token_count: int
    content_token_count: int
    unique_lemmas: int
    content_lemmas: int
    new_lemmas: int
    new_content_lemmas: int
    repeated_content_lemmas: int
    content_reuse_percentage: float
    cumulative_lemmas: int
    cumulative_content_lemmas: int
    unknown_content_lemmas: int | None
    new_unknown_content_lemmas: int | None
    cumulative_unknown_content_lemmas: int | None


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Vocabulary analysis result for one book."""

    book: Book
    scope: AnalysisScope
    total_tokens: int
    content_tokens: int
    unique_words: int
    unique_content_words: int
    unique_lemmas: int
    unique_content_lemmas: int
    learning_min_count: int
    known_profile_enabled: bool
    known_profile_size: int
    known_lemmas: frozenset[str]
    known_content_tokens: int
    section_stats: tuple[SectionStat, ...]
    word_stats: tuple[WordStat, ...]
    lemma_stats: tuple[LemmaStat, ...]
    coverage_stats: tuple[CoverageStat, ...]
    learning_stats: tuple[LearningWordStat, ...]
    progression_stats: tuple[SectionProgressStat, ...]
