"""Command-line interface for LexiSift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lexisift import __version__
from lexisift.analysis import AnalysisError, analyze_book
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
        "--scope",
        choices=[scope.value for scope in AnalysisScope],
        default=AnalysisScope.ALL.value,
        help="Analyze all spine sections or only main content (default: all)",
    )
    return parser


def _run_analyze(epub_path: Path, output_dir: Path, scope: AnalysisScope) -> int:
    book = load_epub(epub_path)
    result = analyze_book(book, scope=scope)
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
    print(f"Reports: {destination}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the LexiSift CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return _run_analyze(args.epub, args.output_dir, AnalysisScope(args.scope))
    except (EpubError, AnalysisError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
