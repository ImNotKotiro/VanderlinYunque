"""Catálogo de libros del servidor y texto como se lee dentro del juego."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

from config import TOOL_ROOT

REPO_ROOT = TOOL_ROOT.parents[1]
DEFAULT_DEFINITIONS = REPO_ROOT / "code" / "game" / "objects" / "items" / "books.dm"
DEFAULT_BOOKS_DIR = REPO_ROOT / "strings" / "books"

_TYPE_LINE = re.compile(r"^/obj/item/book(?:/[A-Za-z0-9_]+)*")
_VAR_LINE = re.compile(r'^\s*(name|desc|bookfile)\s*=\s*"((?:\\.|[^"\\])*)"')
_TAG = re.compile(r"<[^>]+>")
_BREAK = re.compile(r"(?i)<br\s*/?>")
_RULE = re.compile(r"(?i)<hr\s*/?>")
_END_BLOCK = re.compile(r"(?i)</(p|div|h[1-6]|li|tr|blockquote)>")
_LIST_ITEM = re.compile(r"(?i)<li[^>]*>")
_PARAGRAPH = "\x00P\x00"
_LINE = "\x00L\x00"


@dataclass(frozen=True)
class Book:
    title: str
    desc: str
    filename: str
    body: str

    def formatted_text(self) -> str:
        header = [self.title]
        if self.desc:
            header.append(self.desc)
        header.append("─" * max(12, min(len(self.title), 42)))
        return "\n".join(header) + "\n\n" + self.body.strip() + "\n"

    def txt_name(self) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*]', "", self.title)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
        if not cleaned:
            cleaned = Path(self.filename).stem or "libro"
        return cleaned[:80] + ".txt"


class BookLibrary:
    def __init__(self, definitions: Path, folder: Path) -> None:
        self.definitions = definitions
        self.folder = folder

    def catalog(self) -> list[Book]:
        if not self.definitions.is_file() or not self.folder.is_dir():
            return []
        source = self.definitions.read_text(encoding="utf-8", errors="replace")
        found: list[Book] = []
        seen: set[tuple[str, str]] = set()
        for raw in _with_inherited_files(parse_book_types(source)):
            filename = raw["bookfile"]
            if not filename or filename == "filenamehere.json":
                continue
            path = self.folder / filename
            body = read_book_body(path)
            if not body:
                continue
            key = (raw["name"], filename)
            if key in seen:
                continue
            seen.add(key)
            found.append(Book(title=raw["name"], desc=raw["desc"], filename=filename, body=body))
        return sorted(found, key=lambda book: book.title.casefold())

    def find(self, query: str) -> list[Book]:
        needle = _normalize(query)
        if not needle:
            return []
        books = self.catalog()
        exact = [
            book
            for book in books
            if needle in {_normalize(book.title), _normalize(Path(book.filename).stem)}
        ]
        if exact:
            return exact
        return [book for book in books if needle in _normalize(book.title) or needle in _normalize(book.filename)]


def parse_book_types(source: str) -> list[dict[str, str]]:
    current: dict[str, str] | None = None
    found: list[dict[str, str]] = []

    def finish() -> None:
        nonlocal current
        if current and current["name"]:
            found.append(current)
        current = None

    for line in source.splitlines():
        if line.startswith("/obj/item/book"):
            finish()
            path = line.split("//", 1)[0].strip()
            if "/proc/" in path or not _TYPE_LINE.match(path):
                current = None
                continue
            current = {"path": path, "name": "", "desc": "", "bookfile": ""}
            continue
        if current is None:
            continue
        if line and not line[0].isspace():
            finish()
            continue
        match = _VAR_LINE.match(line)
        if match:
            current[match.group(1)] = match.group(2).replace('\\"', '"')
    finish()
    return found


def _with_inherited_files(books: list[dict[str, str]]) -> list[dict[str, str]]:
    by_path = {book["path"]: book for book in books}
    for book in books:
        if book["bookfile"]:
            continue
        parent = book["path"].rsplit("/", 1)[0]
        while parent.startswith("/obj/item/book"):
            ancestor = by_path.get(parent)
            if ancestor and ancestor["bookfile"]:
                book["bookfile"] = ancestor["bookfile"]
                break
            parent = parent.rsplit("/", 1)[0]
    return books


def read_book_body(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        payload = _loads_book_json(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, ValueError):
        return ""
    contents = payload.get("Contents") if isinstance(payload, dict) else None
    if not isinstance(contents, list):
        return ""
    pages = [page for page in contents if isinstance(page, str) and page.strip()]
    if not pages:
        return ""
    # In-game, each page is appended and then a <br> is added.
    return html_fragment_to_text("<br>".join(pages))


def _loads_book_json(text: str) -> object:
    """BYOND's json_decode accepts raw line breaks inside strings."""
    return json.loads(_escape_controls_in_strings(text))


def _escape_controls_in_strings(text: str) -> str:
    out: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                out.append(char)
                escaped = False
                continue
            if char == "\\":
                out.append(char)
                escaped = True
                continue
            if char == '"':
                in_string = False
                out.append(char)
                continue
            if char == "\n":
                out.append("\\n")
                continue
            if char == "\r":
                continue
            if char == "\t":
                out.append("\\t")
                continue
            out.append(char)
            continue
        if char == '"':
            in_string = True
        out.append(char)
    return "".join(out)


def html_fragment_to_text(fragment: str) -> str:
    text = fragment.replace("\r\n", "\n").replace("\r", "\n")
    text = _RULE.sub(_PARAGRAPH, text)
    text = _BREAK.sub(_LINE, text)
    text = _END_BLOCK.sub(_PARAGRAPH, text)
    text = _LIST_ITEM.sub(_LINE + "• ", text)
    # Newlines left in the source are HTML wrapping; a browser collapses them.
    text = text.replace("\n", " ")
    text = _TAG.sub("", text)
    text = html.unescape(text).replace("\xa0", " ")
    text = text.replace(_LINE, "\n").replace(_PARAGRAPH, "\n\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    compact: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if compact and not blank:
                compact.append("")
            blank = True
            continue
        compact.append(line)
        blank = False
    return "\n".join(compact).strip()


def format_catalog(books: list[Book]) -> str:
    if not books:
        return "No hay libros legibles en el servidor."
    lines = [f"{index}. {book.title}" for index, book in enumerate(books, start=1)]
    lines.append("")
    lines.append("Pide uno con /libro y el título.")
    return "\n".join(lines)


def _normalize(value: str) -> str:
    value = value.casefold().replace("'", "")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()
