"""Libros escritos por jugadores, tal como los guarda SSlibrarian en data/player_generated_books."""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from bot.game.books import html_fragment_to_text, loads_byond_json, matches_words, normalize_title

INDEX_NAME = "_book_titles"
DEFAULT_CATEGORY = "Thesis"
DEFAULT_ICON = "basic_book"
#: Las de /obj/item/manuscript en code/game/objects/items/books.dm.
CATEGORIES = ("Apocrypha & Grimoires", "Myths & Tales", "Legends & Accounts", "Thesis", "Eoratica")
#: MAX_CHARTER_LEN y MAX_BOOK_LEN de code/__DEFINES/say.dm.
MAX_TITLE_LEN = 80
MAX_TEXT_LEN = 6000


class PlayerBookError(Exception):
    """El libro no se puede guardar. El mensaje se puede enseñar al jugador."""


def encode_title(title: str) -> str:
    """Igual que url_encode() de BYOND: espacios como + y el resto en %XX."""
    return quote_plus(title, safe="")


def text_to_html(text: str) -> str:
    """Como compila el juego un manuscrito: un <p> por párrafo; los saltos de línea, <br>."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    return "".join(f"<p>{html.escape(part).replace(chr(10), '<br>')}</p>\n" for part in paragraphs)


@dataclass(frozen=True)
class PlayerBook:
    title: str
    author: str
    author_ckey: str
    category: str
    body: str
    filename: str

    def label(self) -> str:
        return f"{self.title} — {self.author}" if self.author else self.title

    def header(self) -> str:
        details = " · ".join(part for part in (self.author, self.category) if part)
        return f"**{self.title}**\n{details}" if details else f"**{self.title}**"


class PlayerBookLibrary:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def problem(self) -> str:
        if not self.folder.is_dir():
            return f"No se encuentra la carpeta de libros de jugadores: {self.folder}"
        return ""

    def catalog(self) -> list[PlayerBook]:
        if self.problem():
            return []
        found: list[PlayerBook] = []
        seen: set[str] = set()
        for name in self._file_names():
            if name == INDEX_NAME or name in seen:
                continue
            seen.add(name)
            book = read_player_book(self.folder / f"{name}.json")
            if book:
                found.append(book)
        return sorted(found, key=lambda book: book.title.casefold())

    def find(self, query: str) -> list[PlayerBook]:
        needle = normalize_title(query)
        if not needle:
            return []
        books = self.catalog()
        exact = [book for book in books if normalize_title(book.title) == needle]
        if exact:
            return exact
        return [book for book in books if matches_words(needle, book.title)]

    def exists(self, title: str) -> bool:
        if (self.folder / f"{encode_title(title)}.json").exists():
            return True
        wanted = normalize_title(title)
        return any(normalize_title(book.title) == wanted for book in self.catalog())

    def save(
        self,
        title: str,
        author: str,
        author_ckey: str,
        text: str,
        category: str,
        icon: str = DEFAULT_ICON,
    ) -> PlayerBook:
        """Escribe el libro y lo añade al índice, como SSlibrarian.playerbook2file()."""
        problem = self.problem()
        if problem:
            raise PlayerBookError(problem)
        title = clean_title(title)
        if category not in CATEGORIES:
            raise PlayerBookError(f"Categoría desconocida. Usa una de estas: {', '.join(CATEGORIES)}.")
        if not text.strip():
            raise PlayerBookError("El libro no tiene texto.")
        if len(text) > MAX_TEXT_LEN:
            raise PlayerBookError(f"El libro pasa de {MAX_TEXT_LEN} caracteres.")
        encoded = encode_title(title)
        path = self.folder / f"{encoded}.json"
        if self.exists(title):
            raise PlayerBookError(f"Ya hay un libro titulado «{title}».")
        names = self._file_names()
        payload = {
            "book_title": title,
            "author": author.strip() or "Unknown",
            "author_ckey": author_ckey,
            "icon": icon,
            "text": text_to_html(text),
            "category": category,
        }
        _write_atomic(path, json.dumps(payload))
        if encoded not in names:
            names.append(encoded)
        _write_atomic(self.folder / f"{INDEX_NAME}.json", json.dumps([name for name in names if name != INDEX_NAME]))
        book = read_player_book(path)
        if book is None:
            raise PlayerBookError("El libro se guardó pero no se pudo leer de vuelta.")
        return book

    def _file_names(self) -> list[str]:
        """El índice del juego manda; sin índice se leen todos los .json de la carpeta."""
        index = self.folder / f"{INDEX_NAME}.json"
        if index.is_file():
            try:
                names = json.loads(index.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                names = None
            if isinstance(names, list):
                return [str(name) for name in names if isinstance(name, str)]
        return sorted(path.stem for path in self.folder.glob("*.json") if path.stem != INDEX_NAME)


def clean_title(title: str) -> str:
    cleaned = " ".join(title.split())
    if not cleaned:
        raise PlayerBookError("El libro necesita un título.")
    if len(cleaned) > MAX_TITLE_LEN:
        raise PlayerBookError(f"El título no puede pasar de {MAX_TITLE_LEN} caracteres.")
    if encode_title(cleaned) == INDEX_NAME:
        raise PlayerBookError("Ese título no está permitido.")
    return cleaned


def _write_atomic(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise PlayerBookError(f"No se pudo escribir {path.name}: {exc}") from exc


def read_player_book(path: Path) -> PlayerBook | None:
    if not path.is_file():
        return None
    try:
        payload = loads_byond_json(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    title = _text(payload.get("book_title"))
    body = html_fragment_to_text(_text(payload.get("text")))
    if not title or not body:
        return None
    return PlayerBook(
        title=title,
        author=_text(payload.get("author")),
        author_ckey=_text(payload.get("author_ckey")),
        category=_text(payload.get("category")) or DEFAULT_CATEGORY,
        body=body,
        filename=path.name,
    )


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
