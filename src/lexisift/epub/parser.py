"""Parse EPUB metadata and extract readable text in spine order."""

from __future__ import annotations

import posixpath
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag
from xml.etree import ElementTree as ET

from lexisift.models import Book, Chapter

_CONTAINER_PATH = "META-INF/container.xml"
_CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
_OPF_NS = "http://www.idpf.org/2007/opf"
_DC_NS = "http://purl.org/dc/elements/1.1/"


class EpubError(RuntimeError):
    """Raised when an EPUB cannot be parsed safely."""


class _XhtmlTextExtractor(HTMLParser):
    """Collect visible text and a useful document title from XHTML/HTML."""

    _IGNORED_TAGS = {"script", "style", "svg"}
    _HEADING_TAGS = {"h1", "h2", "h3"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._heading_depth = 0
        self._title_depth = 0
        self._chunks: list[str] = []
        self._heading_chunks: list[str] = []
        self._title_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag = tag.casefold()
        if tag in self._IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in self._HEADING_TAGS and not self._heading_chunks:
            self._heading_depth += 1
        if tag == "title":
            self._title_depth += 1
        if tag in {"p", "div", "br", "li", "section", "article", "blockquote"} | self._HEADING_TAGS:
            self._chunks.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in self._IGNORED_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in self._HEADING_TAGS and self._heading_depth:
            self._heading_depth -= 1
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in {"p", "div", "li", "section", "article", "blockquote"} | self._HEADING_TAGS:
            self._chunks.append(" ")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if not data.strip():
            return
        if self._title_depth:
            self._title_chunks.append(data)
            return
        self._chunks.append(data)
        if self._heading_depth:
            self._heading_chunks.append(data)

    @property
    def text(self) -> str:
        """Return normalized visible text."""

        return " ".join("".join(self._chunks).split())

    @property
    def title(self) -> str | None:
        """Return the first heading, otherwise the HTML title."""

        heading = " ".join("".join(self._heading_chunks).split())
        if heading:
            return heading
        title = " ".join("".join(self._title_chunks).split())
        return title or None


def _read_xml(epub: zipfile.ZipFile, path: str) -> ET.Element:
    try:
        payload = epub.read(path)
    except KeyError as exc:
        raise EpubError(f"EPUB is missing required file: {path}") from exc
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise EpubError(f"Invalid XML in EPUB file: {path}") from exc


def _find_opf_path(epub: zipfile.ZipFile) -> str:
    root = _read_xml(epub, _CONTAINER_PATH)
    node = root.find(f".//{{{_CONTAINER_NS}}}rootfile")
    if node is None:
        raise EpubError("EPUB container.xml does not contain a rootfile")
    full_path = node.attrib.get("full-path")
    if not full_path:
        raise EpubError("EPUB rootfile is missing its full-path attribute")
    return unquote(full_path)


def _metadata_text(root: ET.Element, tag: str) -> str | None:
    node = root.find(f".//{{{_DC_NS}}}{tag}")
    if node is None or node.text is None:
        return None
    value = " ".join(node.text.split())
    return value or None


def _resolve_member(opf_path: str, href: str) -> str:
    href_without_fragment = urldefrag(href).url
    decoded_href = unquote(href_without_fragment)
    base = posixpath.dirname(opf_path)
    return posixpath.normpath(posixpath.join(base, decoded_href))


def _decode_document(payload: bytes) -> str:
    # UTF-8 is required by modern EPUB content; utf-8-sig also tolerates BOMs.
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Older EPUBs occasionally contain an XML-declared legacy encoding.
        declaration = payload[:200].decode("ascii", errors="ignore")
        marker = "encoding=\""
        if marker in declaration:
            encoding = declaration.split(marker, 1)[1].split("\"", 1)[0]
            try:
                return payload.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        return payload.decode("utf-8", errors="replace")


def _extract_document(payload: bytes, fallback_title: str) -> tuple[str, str]:
    parser = _XhtmlTextExtractor()
    parser.feed(_decode_document(payload))
    parser.close()
    return parser.text, parser.title or fallback_title


def load_epub(path: str | Path) -> Book:
    """Load an EPUB and return readable documents in declared spine order."""

    epub_path = Path(path).expanduser().resolve()
    if not epub_path.is_file():
        raise EpubError(f"EPUB file does not exist: {epub_path}")

    try:
        epub = zipfile.ZipFile(epub_path)
    except zipfile.BadZipFile as exc:
        raise EpubError(f"Not a valid EPUB/ZIP file: {epub_path}") from exc

    with epub:
        opf_path = _find_opf_path(epub)
        package = _read_xml(epub, opf_path)

        manifest: dict[str, tuple[str, str]] = {}
        for item in package.findall(f".//{{{_OPF_NS}}}manifest/{{{_OPF_NS}}}item"):
            item_id = item.attrib.get("id")
            href = item.attrib.get("href")
            media_type = item.attrib.get("media-type", "")
            if item_id and href:
                manifest[item_id] = (href, media_type)

        chapters: list[Chapter] = []
        for order, itemref in enumerate(
            package.findall(f".//{{{_OPF_NS}}}spine/{{{_OPF_NS}}}itemref"), start=1
        ):
            idref = itemref.attrib.get("idref")
            if not idref or idref not in manifest:
                continue
            href, media_type = manifest[idref]
            if media_type not in {"application/xhtml+xml", "text/html"}:
                continue

            member = _resolve_member(opf_path, href)
            try:
                payload = epub.read(member)
            except KeyError as exc:
                raise EpubError(f"Spine item is missing from EPUB archive: {member}") from exc

            text, title = _extract_document(payload, fallback_title=Path(member).stem)
            if not text:
                continue
            chapters.append(
                Chapter(
                    chapter_id=idref,
                    order=len(chapters) + 1,
                    href=member,
                    title=title,
                    text=text,
                )
            )

        if not chapters:
            raise EpubError("No readable XHTML/HTML documents were found in the EPUB spine")

        title = _metadata_text(package, "title") or epub_path.stem
        author = _metadata_text(package, "creator")
        return Book(
            title=title,
            author=author,
            source_path=str(epub_path),
            chapters=tuple(chapters),
        )
