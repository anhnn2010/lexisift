"""Integration test for the minimal EPUB parser."""

from __future__ import annotations

import zipfile
from pathlib import Path

from lexisift.epub import load_epub


def _write_test_epub(path: Path) -> None:
    container = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
    opf = """<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
    <dc:creator>Test Author</dc:creator>
  </metadata>
  <manifest>
    <item id="c1" href="text/ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="text/ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="c2"/>
    <itemref idref="c1"/>
  </spine>
</package>
"""
    chapter1 = """<html><head><title>Fallback One</title></head><body><h1>First</h1><p>Hello one.</p></body></html>"""
    chapter2 = """<html><head><title>Fallback Two</title></head><body><h1>Second</h1><p>Hello two.</p></body></html>"""

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/text/ch1.xhtml", chapter1)
        archive.writestr("OEBPS/text/ch2.xhtml", chapter2)


def test_load_epub_follows_spine_order(tmp_path: Path) -> None:
    epub_path = tmp_path / "book.epub"
    _write_test_epub(epub_path)

    book = load_epub(epub_path)

    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert [chapter.chapter_id for chapter in book.chapters] == ["c2", "c1"]
    assert [chapter.title for chapter in book.chapters] == ["Second", "First"]


def test_html_title_is_not_in_visible_chapter_text(tmp_path: Path) -> None:
    epub_path = tmp_path / "book.epub"
    _write_test_epub(epub_path)

    book = load_epub(epub_path)

    assert "Fallback Two" not in book.chapters[0].text
    assert "Hello two." in book.chapters[0].text
