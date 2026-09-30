"""Write human-readable and CSV vocabulary reports."""

from __future__ import annotations

import csv
from pathlib import Path

from lexisift.models import AnalysisResult, SectionKind


def _write_vocabulary_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["word", "count", "section_count", "first_seen_section", "percentage"]
        )
        for stat in result.word_stats:
            writer.writerow(
                [
                    stat.word,
                    stat.count,
                    stat.section_count,
                    stat.first_seen_section,
                    f"{stat.percentage:.6f}",
                ]
            )


def _write_sections_csv(result: AnalysisResult, path: Path) -> None:
    stats_by_id = {stat.section_id: stat for stat in result.section_stats}
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["order", "section_id", "type", "included", "token_count", "title", "href"]
        )
        for section in result.book.sections:
            stat = stats_by_id[section.section_id]
            writer.writerow(
                [
                    section.order,
                    section.section_id,
                    section.kind.value,
                    "yes" if stat.included else "no",
                    stat.token_count,
                    section.title,
                    section.href,
                ]
            )


def _write_summary(result: AnalysisResult, path: Path) -> None:
    author = result.book.author or "Unknown"
    main_chapters = sum(
        1 for section in result.book.sections if section.kind is SectionKind.CHAPTER
    )
    included_sections = sum(1 for stat in result.section_stats if stat.included)
    lines = [
        "LexiSift analysis",
        "=================",
        f"Title: {result.book.title}",
        f"Author: {author}",
        f"Scope: {result.scope.value}",
        f"Spine sections: {len(result.book.sections)}",
        f"Main chapters: {main_chapters}",
        f"Analyzed sections: {included_sections}",
        f"Total word tokens: {result.total_tokens}",
        f"Unique normalized words: {result.unique_words}",
        "",
        "Top 20 words:",
    ]
    for index, stat in enumerate(result.word_stats[:20], start=1):
        lines.append(
            f"{index:>2}. {stat.word:<24} {stat.count:>7} "
            f"({stat.section_count} sections, {stat.percentage:.3f}%)"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reports(result: AnalysisResult, output_dir: str | Path) -> Path:
    """Write analysis artifacts and return the output directory."""

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    _write_vocabulary_csv(result, destination / "vocabulary.csv")
    _write_sections_csv(result, destination / "sections.csv")
    _write_summary(result, destination / "summary.txt")
    return destination
