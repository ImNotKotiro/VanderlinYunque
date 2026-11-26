"""Biblioteca del servidor: listados de libros y envío de uno por mensaje privado."""

from __future__ import annotations

from collections.abc import Mapping

from bot.config import Config
from bot.features.base import Feature, FeatureResult, Requester
from bot.formatting import split_text
from bot.game.books import (
    DEFAULT_BOOKS_DIR,
    DEFAULT_DEFINITIONS,
    Book,
    BookLibrary,
    format_catalog,
    normalize_title,
)
from bot.game.player_books import PlayerBook, PlayerBookLibrary
from bot.server.gateway import ServerGateway

CATALOG_COLOR = 0x6B4F3A
BOOK_COLOR = 0xC6A15B
PLAYER_BOOK_MESSAGE_LIMIT = 500
MAX_LISTED_MATCHES = 12

CODE_SHELF = "codigo"
PLAYER_SHELF = "jugadores"
SHELVES: tuple[tuple[str, str], ...] = (
    (CODE_SHELF, "Libros del código"),
    ("trabajos", "Libros de trabajos"),
    (PLAYER_SHELF, "Libros de jugadores"),
)
#: Listados en los que busca /libro, en este orden.
REQUESTABLE_SHELVES = (CODE_SHELF, PLAYER_SHELF)

Library = BookLibrary | PlayerBookLibrary


def default_libraries(config: Config | None = None) -> dict[str, Library]:
    """Los listados sin entrada aquí responden que aún no están disponibles."""
    libraries: dict[str, Library] = {CODE_SHELF: BookLibrary(DEFAULT_DEFINITIONS, DEFAULT_BOOKS_DIR)}
    if config is not None:
        libraries[PLAYER_SHELF] = PlayerBookLibrary(config.player_books_dir)
    return libraries


class BooksFeature(Feature):
    id = "books"
    command_names = ("biblioteca", "libro")
    description = "Consulta la biblioteca del servidor."

    def __init__(self, libraries: Mapping[str, Library] | None = None) -> None:
        self.libraries = dict(libraries if libraries is not None else default_libraries())

    def command_description(self, name: str) -> str:
        if name == "libro":
            return "Te envía un libro del código o de jugadores por mensaje privado."
        return "Lista los libros del servidor: del código, de trabajos o de jugadores."

    def command_argument(self, name: str) -> str | None:
        if name == "libro":
            return "titulo"
        return "listado"

    def command_argument_description(self, name: str) -> str:
        if name == "libro":
            return "Título del libro, o parte de él."
        return "Qué listado quieres ver."

    def command_choices(self, name: str) -> tuple[tuple[str, str], ...]:
        if name == "biblioteca":
            return SHELVES
        return ()

    def reply_is_ephemeral(self, name: str) -> bool:
        return name in {"biblioteca", "libro"}

    def run(
        self,
        gateway: ServerGateway,
        config: Config,
        command: str = "",
        argument: str = "",
        requester: Requester | None = None,
        extra: str = "",
    ) -> FeatureResult:
        if command == "libro":
            return self._request_book(argument)
        return self._shelf_listing(argument)

    def _shelf_listing(self, argument: str) -> FeatureResult:
        wanted = argument.strip().casefold()
        shelf = next(
            ((key, label) for key, label in SHELVES if wanted in {key, label.casefold()}),
            None,
        )
        if shelf is None:
            options = "\n".join(f"• {key}: {label}" for key, label in SHELVES)
            return _reply(f"Elige un listado:\n{options}")
        key, label = shelf
        library = self.libraries.get(key)
        if library is None:
            return _reply(f"{label}: este listado todavía no está disponible.")
        problem = library.problem()
        if problem:
            return _reply(f"{label}: {problem}")
        books = library.catalog()
        footer = "Pide uno con /libro y el título." if key in REQUESTABLE_SHELVES else ""
        listing = format_catalog([book.label() for book in books], footer)
        return FeatureResult(
            ok=bool(books),
            text=f"{label}\n\n{listing}",
            announce=False,
            ephemeral=True,
            embed_title=label,
            embed_description=listing[:4000],
            embed_color=CATALOG_COLOR,
            embed_footer=f"{len(books)} libro" if len(books) == 1 else f"{len(books)} libros",
        )

    def _request_book(self, argument: str) -> FeatureResult:
        query = argument.strip()
        if not query:
            return _reply("Escribe el título. Ejemplo: /libro Tome of Justice")
        labels = dict(SHELVES)
        matches: list[tuple[str, Book | PlayerBook]] = []
        for key in REQUESTABLE_SHELVES:
            library = self.libraries.get(key)
            if library is not None:
                matches.extend((key, book) for book in library.find(query))
        exact = [match for match in matches if normalize_title(match[1].title) == normalize_title(query)]
        if len(exact) == 1:
            matches = exact
        if not matches:
            return _reply(
                f"No encontré ningún libro que coincida con «{query}». Mira la lista con /biblioteca."
            )
        if len(matches) > 1:
            names = "\n".join(
                f"• {book.title} ({labels[key]})" for key, book in matches[:MAX_LISTED_MATCHES]
            )
            hidden = len(matches) - MAX_LISTED_MATCHES
            extra = f"\n… y {hidden} más." if hidden > 0 else ""
            return _reply(f"Hay varios libros con «{query}». Precisa el título:\n{names}{extra}")
        _, book = matches[0]
        if isinstance(book, PlayerBook):
            return _player_book(book)
        return _code_book(book)


def _code_book(book: Book) -> FeatureResult:
    document = book.formatted_text()
    return FeatureResult(
        ok=True,
        text=document,
        announce=False,
        ephemeral=True,
        private=True,
        embed_title=book.title,
        embed_description=f"Te envié **{book.title}** por mensaje privado.",
        embed_color=BOOK_COLOR,
        attachment_name=book.txt_name(),
        attachment_text=document,
    )


def _player_book(book: PlayerBook) -> FeatureResult:
    messages = (book.header(), *split_text(book.body, PLAYER_BOOK_MESSAGE_LIMIT))
    return FeatureResult(
        ok=True,
        text="\n\n".join(messages),
        announce=False,
        ephemeral=True,
        private=True,
        embed_title=book.title,
        embed_description=f"Te envié **{book.title}** por mensaje privado.",
        embed_color=BOOK_COLOR,
        private_messages=messages,
    )


def _reply(text: str) -> FeatureResult:
    return FeatureResult(ok=False, text=text, announce=False, ephemeral=True)
