"""Command-line interface for LexiSift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lexisift import __version__
from lexisift.analysis import analyze_book
from lexisift.epub import EpubError, load_epub
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
    return parser


def _run_analyze(epub_path: Path, output_dir: Path) -> int:
    book = load_epub(epub_path)
    result = analyze_book(book)
    destination = write_reports(result, output_dir)

    author = book.author or "Unknown"
    print(f"Title: {book.title}")
    print(f"Author: {author}")
    print(f"Chapters: {len(book.chapters)}")
    print(f"Total word tokens: {result.total_tokens}")
    print(f"Unique normalized words: {result.unique_words}")
    print(f"Reports: {destination}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the LexiSift CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return _run_analyze(args.epub, args.output_dir)
    except EpubError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
