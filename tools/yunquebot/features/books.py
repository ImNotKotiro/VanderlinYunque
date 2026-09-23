"""Lista de libros del servidor y envío de uno en texto."""

from __future__ import annotations

from books import DEFAULT_BOOKS_DIR, DEFAULT_DEFINITIONS, BookLibrary, format_catalog
from config import Config
from features.base import Feature, FeatureResult
from gateway import ServerGateway

CATALOG_COLOR = 0x6B4F3A
BOOK_COLOR = 0xC6A15B


class BooksFeature(Feature):
    id = "books"
    command_names = ("libros", "libro")
    description = "Lista los libros del servidor."

    def __init__(self, library: BookLibrary | None = None) -> None:
        self.library = library or BookLibrary(DEFAULT_DEFINITIONS, DEFAULT_BOOKS_DIR)

    def command_description(self, name: str) -> str:
        if name == "libro":
            return "Te envía un libro del servidor por mensaje privado."
        return "Lista los libros que hay en el servidor."

    def command_argument(self, name: str) -> str | None:
        if name == "libro":
            return "titulo"
        return None

    def reply_is_ephemeral(self, name: str) -> bool:
        return name in {"libros", "libro"}

    def run(
        self,
        gateway: ServerGateway,
        config: Config,
        command: str = "",
        argument: str = "",
    ) -> FeatureResult:
        books = self.library.catalog()
        if command == "libro":
            return _request_book(self.library, argument)

        listing = format_catalog(books)
        return FeatureResult(
            ok=bool(books),
            text=listing,
            announce=False,
            ephemeral=True,
            embed_title="Libros del servidor",
            embed_description=listing[:4000],
            embed_color=CATALOG_COLOR,
            embed_footer="Pide uno con /libro",
        )


def _request_book(library: BookLibrary, argument: str) -> FeatureResult:
    query = argument.strip()
    if not query:
        return FeatureResult(
            ok=False,
            text="Escribe el título. Ejemplo: /libro Tome of Justice",
            announce=False,
            ephemeral=True,
        )
    matches = library.find(query)
    if not matches:
        return FeatureResult(
            ok=False,
            text=f"No encontré ningún libro que coincida con «{query}». Mira la lista con /libros.",
            announce=False,
            ephemeral=True,
        )
    if len(matches) > 1:
        names = "\n".join(f"• {book.title}" for book in matches[:12])
        extra = "" if len(matches) <= 12 else f"\n… y {len(matches) - 12} más."
        return FeatureResult(
            ok=False,
            text=f"Hay varios libros con «{query}». Precisa el título:\n{names}{extra}",
            announce=False,
            ephemeral=True,
        )
    book = matches[0]
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

