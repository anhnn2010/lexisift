"""Tests for fallback section classification used by EPUB 2 style books."""

from lexisift.epub.section_classifier import classify_section
from lexisift.models import SectionKind


def _classify(section_id: str, title: str) -> SectionKind:
    return classify_section(
        section_id=section_id,
        title=title,
        href=f"OEBPS/{section_id}.xhtml",
        semantics=frozenset(),
    )


def test_classifies_whole_brain_style_section_ids_and_titles() -> None:
    samples = {
        ("toc", "Contents"): SectionKind.TOC,
        ("itr", "INTRODUCTION:"): SectionKind.INTRODUCTION,
        ("c01", "CHAPTER 1"): SectionKind.CHAPTER,
        ("c06", "CHAPTER 6"): SectionKind.CHAPTER,
        ("bm1", "CONCLUSION"): SectionKind.CONCLUSION,
        ("bm2", "REFRIGERATOR SHEET"): SectionKind.BACKMATTER,
        ("bm3", "Whole-Brain Ages and Stages"): SectionKind.BACKMATTER,
        ("ded", "Book Title"): SectionKind.DEDICATION,
        ("ack", "Acknowledgments"): SectionKind.ACKNOWLEDGMENTS,
        ("ata", "ABOUT THE AUTHORS"): SectionKind.ABOUT_AUTHOR,
    }

    for (section_id, title), expected in samples.items():
        assert _classify(section_id, title) is expected
