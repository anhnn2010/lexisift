"""Command-line interface for LexiSift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lexisift import __version__
from lexisift.analysis import AnalysisError, KnownWordsError, analyze_book, load_known_words
from lexisift.epub import EpubError, load_epub
from lexisift.models import AnalysisScope, SectionKind
from lexisift.reporting import write_reports


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lexisift",
        description="Understand the vocabulary behind a book.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Analyze vocabulary in an EPUB file")
    analyze.add_argument("epub", type=Path, help="Path to the EPUB file")
    analyze.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("lexisift-output"),
        help="Report directory (default: ./lexisift-output)",
    )
    analyze.add_argument(
        "--learning-min-count",
        type=int,
        default=3,
        help="Minimum book occurrences for learning_words.csv (default: 3)",
    )
    analyze.add_argument(
        "--known-words",
        type=Path,
        default=None,
        help="UTF-8 file with one known word/lemma per line",
    )
    analyze.add_argument(
        "--scope",
        choices=[scope.value for scope in AnalysisScope],
        default=AnalysisScope.ALL.value,
        help="Analyze all spine sections or only main content (default: all)",
    )
    return parser


def _run_analyze(
    epub_path: Path,
    output_dir: Path,
    scope: AnalysisScope,
    learning_min_count: int,
    known_words_path: Path | None,
) -> int:
    book = load_epub(epub_path)
    known_words = load_known_words(known_words_path) if known_words_path is not None else None
    result = analyze_book(
        book,
        scope=scope,
        learning_min_count=learning_min_count,
        known_words=known_words,
    )
    destination = write_reports(result, output_dir)

    author = book.author or "Unknown"
    main_chapters = sum(1 for section in book.sections if section.kind is SectionKind.CHAPTER)
    analyzed_sections = sum(1 for stat in result.section_stats if stat.included)
    print(f"Title: {book.title}")
    print(f"Author: {author}")
    print(f"Scope: {scope.value}")
    print(f"Spine sections: {len(book.sections)}")
    print(f"Main chapters: {main_chapters}")
    print(f"Analyzed sections: {analyzed_sections}")
    print(f"Total word tokens: {result.total_tokens}")
    print(f"Unique normalized words: {result.unique_words}")
    print(f"Unique lemmas: {result.unique_lemmas}")
    print(f"Unique content lemmas: {result.unique_content_lemmas}")
    proper_nouns = sum(1 for stat in result.lemma_stats if stat.is_proper_noun)
    print(f"Likely proper-noun lemmas: {proper_nouns}")
    if result.known_profile_enabled:
        known_content_lemmas = sum(
            1
            for stat in result.lemma_stats
            if not stat.is_stopword and stat.lemma in result.known_lemmas
        )
        known_content_coverage = (
            result.known_content_tokens / result.content_tokens * 100.0
            if result.content_tokens
            else 0.0
        )
        estimated_reading_tokens = (
            result.total_tokens - result.content_tokens + result.known_content_tokens
        )
        estimated_reading_coverage = (
            estimated_reading_tokens / result.total_tokens * 100.0
            if result.total_tokens
            else 0.0
        )
        print(f"Known-word profile entries: {result.known_profile_size}")
        print(f"Known content lemmas in book: {known_content_lemmas}")
        print(f"Known content-token coverage: {known_content_coverage:.2f}%")
        print(f"Estimated reading-token coverage: {estimated_reading_coverage:.2f}%")
    print(
        f"Learning candidates (count >= {result.learning_min_count}): "
        f"{len(result.learning_stats)}"
    )
    print(f"Reports: {destination}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the LexiSift CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return _run_analyze(
                args.epub,
                args.output_dir,
                AnalysisScope(args.scope),
                args.learning_min_count,
                args.known_words,
            )
    except (EpubError, AnalysisError, KnownWordsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
