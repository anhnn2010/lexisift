"""Write human-readable and CSV vocabulary reports."""

from __future__ import annotations

import csv
from pathlib import Path

from lexisift.models import AnalysisResult, SectionKind


def _write_vocabulary_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "word",
                "lemma",
                "is_stopword",
                "count",
                "section_count",
                "first_seen_section",
                "percentage",
            ]
        )
        for stat in result.word_stats:
            writer.writerow(
                [
                    stat.word,
                    stat.lemma,
                    "yes" if stat.is_stopword else "no",
                    stat.count,
                    stat.section_count,
                    stat.first_seen_section,
                    f"{stat.percentage:.6f}",
                ]
            )


def _write_content_words_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["word", "lemma", "count", "section_count", "first_seen_section", "percentage"]
        )
        for stat in result.word_stats:
            if stat.is_stopword:
                continue
            writer.writerow(
                [
                    stat.word,
                    stat.lemma,
                    stat.count,
                    stat.section_count,
                    stat.first_seen_section,
                    f"{stat.percentage:.6f}",
                ]
            )


def _write_lemmas_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "lemma",
                "is_stopword",
                "count",
                "section_count",
                "first_seen_section",
                "percentage",
                "forms",
            ]
        )
        for stat in result.lemma_stats:
            writer.writerow(
                [
                    stat.lemma,
                    "yes" if stat.is_stopword else "no",
                    stat.count,
                    stat.section_count,
                    stat.first_seen_section,
                    f"{stat.percentage:.6f}",
                    " | ".join(stat.forms),
                ]
            )


def _write_learning_words_csv(result: AnalysisResult, path: Path) -> None:
    """Write ranked, repeated content lemmas intended for learning review."""

    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "rank",
                "lemma",
                "count",
                "section_count",
                "section_coverage_percentage",
                "first_seen_section",
                "book_percentage",
                "priority_score",
                "forms",
            ]
        )
        for stat in result.learning_stats:
            writer.writerow(
                [
                    stat.rank,
                    stat.lemma,
                    stat.count,
                    stat.section_count,
                    f"{stat.section_coverage_percentage:.2f}",
                    stat.first_seen_section,
                    f"{stat.book_percentage:.6f}",
                    f"{stat.priority_score:.3f}",
                    " | ".join(stat.forms),
                ]
            )


def _write_coverage_csv(result: AnalysisResult, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["rank", "lemma", "count", "cumulative_count", "cumulative_percentage"]
        )
        for stat in result.coverage_stats:
            writer.writerow(
                [
                    stat.rank,
                    stat.lemma,
                    stat.count,
                    stat.cumulative_count,
                    f"{stat.cumulative_percentage:.6f}",
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


def _coverage_at(result: AnalysisResult, rank: int) -> float | None:
    """Return cumulative coverage at a rank, or ``None`` when the book has fewer lemmas."""

    if rank <= 0 or rank > len(result.coverage_stats):
        return None
    return result.coverage_stats[rank - 1].cumulative_percentage


def _write_summary(result: AnalysisResult, path: Path) -> None:
    author = result.book.author or "Unknown"
    main_chapters = sum(
        1 for section in result.book.sections if section.kind is SectionKind.CHAPTER
    )
    included_sections = sum(1 for stat in result.section_stats if stat.included)
    content_share = (
        result.content_tokens / result.total_tokens * 100.0 if result.total_tokens else 0.0
    )
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
        f"Content-word tokens: {result.content_tokens} ({content_share:.1f}%)",
        f"Unique normalized words: {result.unique_words}",
        f"Unique content words: {result.unique_content_words}",
        f"Unique lemmas: {result.unique_lemmas}",
        f"Unique content lemmas: {result.unique_content_lemmas}",
        f"Learning candidates (count >= {result.learning_min_count}): {len(result.learning_stats)}",
        "",
        "Lemma coverage:",
    ]
    for rank in (100, 500, 1000, 2000):
        coverage = _coverage_at(result, rank)
        if coverage is not None:
            lines.append(f"Top {rank:>4} lemmas: {coverage:>6.2f}%")

    lines.extend(["", "Top 20 content lemmas:"])
    content_lemmas = [stat for stat in result.lemma_stats if not stat.is_stopword]
    for index, stat in enumerate(content_lemmas[:20], start=1):
        forms = ", ".join(stat.forms[:4])
        if len(stat.forms) > 4:
            forms += ", ..."
        lines.append(
            f"{index:>2}. {stat.lemma:<24} {stat.count:>7} "
            f"({stat.section_count} sections; forms: {forms})"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reports(result: AnalysisResult, output_dir: str | Path) -> Path:
    """Write analysis artifacts and return the output directory."""

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    _write_vocabulary_csv(result, destination / "vocabulary.csv")
    _write_content_words_csv(result, destination / "content_words.csv")
    _write_lemmas_csv(result, destination / "lemmas.csv")
    _write_learning_words_csv(result, destination / "learning_words.csv")
    _write_coverage_csv(result, destination / "coverage.csv")
    _write_sections_csv(result, destination / "sections.csv")
    _write_summary(result, destination / "summary.txt")
    return destination
