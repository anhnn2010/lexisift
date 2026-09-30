"""Write human-readable and CSV vocabulary reports."""

from __future__ import annotations

import csv
from pathlib import Path

from lexisift.models import AnalysisResult


def _write_vocabulary_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["word", "count", "chapter_count", "percentage"])
        for stat in result.word_stats:
            writer.writerow(
                [stat.word, stat.count, stat.chapter_count, f"{stat.percentage:.6f}"]
            )


def _write_chapters_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["order", "chapter_id", "title", "href"])
        for chapter in result.book.chapters:
            writer.writerow([chapter.order, chapter.chapter_id, chapter.title, chapter.href])


def _write_summary(result: AnalysisResult, path: Path) -> None:
    author = result.book.author or "Unknown"
    lines = [
        "LexiSift analysis",
        "=================",
        f"Title: {result.book.title}",
        f"Author: {author}",
        f"Chapters: {len(result.book.chapters)}",
        f"Total word tokens: {result.total_tokens}",
        f"Unique normalized words: {result.unique_words}",
        "",
        "Top 20 words:",
    ]
    for index, stat in enumerate(result.word_stats[:20], start=1):
        lines.append(
            f"{index:>2}. {stat.word:<24} {stat.count:>7} "
            f"({stat.chapter_count} chapters, {stat.percentage:.3f}%)"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reports(result: AnalysisResult, output_dir: str | Path) -> Path:
    """Write v0.1 analysis artifacts and return the output directory."""

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    _write_vocabulary_csv(result, destination / "vocabulary.csv")
    _write_chapters_csv(result, destination / "chapters.csv")
    _write_summary(result, destination / "summary.txt")
    return destination
