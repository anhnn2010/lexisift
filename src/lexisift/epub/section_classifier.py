"""Classify EPUB spine documents into useful semantic section kinds."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from lexisift.models import SectionKind

_CHAPTER_TITLE_RE = re.compile(r"\bchapter\s+(?:\d+|[ivxlcdm]+)\b", re.IGNORECASE)
_CHAPTER_ID_RE = re.compile(r"^(?:c|ch|chap|chapter)[-_]?\d+$", re.IGNORECASE)

_SEMANTIC_KIND: dict[str, SectionKind] = {
    "titlepage": SectionKind.TITLE_PAGE,
    "title-page": SectionKind.TITLE_PAGE,
    "copyright-page": SectionKind.COPYRIGHT,
    "copyright": SectionKind.COPYRIGHT,
    "dedication": SectionKind.DEDICATION,
    "toc": SectionKind.TOC,
    "table-of-contents": SectionKind.TOC,
    "introduction": SectionKind.INTRODUCTION,
    "preamble": SectionKind.INTRODUCTION,
    "chapter": SectionKind.CHAPTER,
    "conclusion": SectionKind.CONCLUSION,
    "epilogue": SectionKind.CONCLUSION,
    "appendix": SectionKind.APPENDIX,
    "acknowledgments": SectionKind.ACKNOWLEDGMENTS,
    "acknowledgements": SectionKind.ACKNOWLEDGMENTS,
    "about-the-author": SectionKind.ABOUT_AUTHOR,
    "about-author": SectionKind.ABOUT_AUTHOR,
}


def _normalized_key(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())


def classify_section(
    *,
    section_id: str,
    title: str,
    href: str,
    semantics: frozenset[str],
) -> SectionKind:
    """Classify a spine document using EPUB semantics first, then safe heuristics.

    EPUB ``epub:type`` metadata is preferred when present. Filename, manifest ID,
    and visible title heuristics provide a fallback for EPUB 2 and lightly marked-up
    commercial books.
    """

    for semantic in semantics:
        kind = _SEMANTIC_KIND.get(semantic.casefold())
        if kind is not None:
            return kind

    if "frontmatter" in semantics:
        return SectionKind.FRONTMATTER
    if "backmatter" in semantics:
        return SectionKind.BACKMATTER

    basename = PurePosixPath(href).stem
    normalized_id = _normalized_key(section_id)
    normalized_title = _normalized_key(title)
    normalized_href = _normalized_key(basename)
    combined = f"{normalized_id} {normalized_title} {normalized_href}"

    if "contents" in normalized_title or normalized_id in {"toc", "contents"}:
        return SectionKind.TOC
    if "introduction" in combined or normalized_id in {"intro", "itr"}:
        return SectionKind.INTRODUCTION
    if _CHAPTER_TITLE_RE.search(title) or _CHAPTER_ID_RE.fullmatch(section_id):
        return SectionKind.CHAPTER
    if "conclusion" in combined or "epilogue" in combined:
        return SectionKind.CONCLUSION
    if "appendix" in combined:
        return SectionKind.APPENDIX
    if "acknowledgment" in combined or "acknowledgement" in combined or normalized_id == "ack":
        return SectionKind.ACKNOWLEDGMENTS
    if "about the author" in combined or "about author" in combined or normalized_id == "ata":
        return SectionKind.ABOUT_AUTHOR
    if "dedication" in combined or normalized_id in {"ded", "dedication"}:
        return SectionKind.DEDICATION
    if "copyright" in combined or normalized_id in {"cop", "copyright"}:
        return SectionKind.COPYRIGHT
    if "title page" in combined or normalized_id in {"titlepage", "tp"}:
        return SectionKind.TITLE_PAGE
    if normalized_id.startswith("fm"):
        return SectionKind.FRONTMATTER
    if normalized_id.startswith("bm"):
        return SectionKind.BACKMATTER
    return SectionKind.OTHER
