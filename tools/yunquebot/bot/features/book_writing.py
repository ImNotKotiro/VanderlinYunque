"""Escribir un libro de jugador: título al empezar, texto en mensajes sueltos y categoría al terminar.

Los administradores pueden banear a quien no deba añadir libros.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field

from bot.config import Config
from bot.features.base import Feature, FeatureResult, Requester, TextCapture
from bot.features.writer_bans import WriterBans
from bot.game.player_books import (
    CATEGORIES,
    MAX_TEXT_LEN,
    PlayerBookError,
    PlayerBookLibrary,
    clean_title,
)
from bot.server.gateway import ServerGateway

START = "escribir_libro"
FINISH = "terminar_libro"
CANCEL = "cancelar_libro"
BAN = "banear_escritor"
UNBAN = "desbanear_escritor"
BANNED = "escritores_baneados"
PARAGRAPH_BREAK = "\n\n"
BANNED_REPLY = "Un administrador te ha prohibido añadir libros a la biblioteca."
_DISCORD_USER = re.compile(r"(?:discord:|<@!?)?(\d{1,25})>?")


@dataclass
class Draft:
    title: str
    author: str
    parts: list[str] = field(default_factory=list)

    def text(self) -> str:
        return PARAGRAPH_BREAK.join(self.parts)


class BookWritingFeature(Feature):
    """Los borradores viven en memoria: se pierden si el bot se reinicia."""

    id = "book_writing"
    command_names = (START, FINISH, CANCEL, BAN, UNBAN, BANNED)
    admin_command_names = (BAN, UNBAN, BANNED)
    description = "Escribe un libro para la biblioteca de jugadores."

    def __init__(self, library: PlayerBookLibrary, bans: WriterBans | None = None) -> None:
        self.library = library
        self.bans = bans if bans is not None else WriterBans()
        self._drafts: dict[str, Draft] = {}
        self._lock = threading.Lock()

    def command_description(self, name: str) -> str:
        if name == START:
            return "Empieza un libro para la biblioteca de jugadores. Luego envíame el texto por privado."
        if name == FINISH:
            return "Guarda en la biblioteca de jugadores el libro que estás escribiendo."
        if name == BAN:
            return "Administradores: impide a alguien añadir libros a la biblioteca de jugadores."
        if name == UNBAN:
            return "Administradores: deja que alguien vuelva a añadir libros."
        if name == BANNED:
            return "Administradores: lista a quién se le ha prohibido añadir libros."
        return "Descarta el libro que estás escribiendo."

    def command_argument(self, name: str) -> str | None:
        if name == START:
            return "titulo"
        if name == FINISH:
            return "categoria"
        if name in (BAN, UNBAN):
            return "usuario"
        return None

    def command_argument_is_user(self, name: str) -> bool:
        return name in (BAN, UNBAN)

    def command_argument_description(self, name: str) -> str:
        if name == START:
            return "Título del libro."
        if name == BAN:
            return "Quién no podrá añadir libros."
        if name == UNBAN:
            return "Quién podrá volver a añadir libros."
        return "Categoría del libro en la biblioteca."

    def command_choices(self, name: str) -> tuple[tuple[str, str], ...]:
        if name == FINISH:
            return tuple((category, category) for category in CATEGORIES)
        return ()

    def reply_is_ephemeral(self, name: str) -> bool:
        return True

    def draft_for(self, requester: Requester) -> Draft | None:
        with self._lock:
            return self._drafts.get(requester.key)

    def run(
        self,
        gateway: ServerGateway,
        config: Config,
        command: str = "",
        argument: str = "",
        requester: Requester | None = None,
    ) -> FeatureResult:
        if requester is None:
            return _reply("Este comando necesita saber quién lo usa.")
        if command == START:
            return self._start(requester, argument)
        if command == FINISH:
            return self._finish(requester, argument)
        if command == BAN:
            return self._ban(config, requester, argument)
        if command == UNBAN:
            return self._unban(argument)
        if command == BANNED:
            return self._list_bans()
        return self._cancel(requester)

    def capture_text(self, requester: Requester, text: str) -> TextCapture | None:
        with self._lock:
            draft = self._drafts.get(requester.key)
            if draft is None:
                return None
            piece = text.strip()
            if not piece:
                return TextCapture(False, "Solo puedo guardar texto, o un archivo .txt.")
            current = draft.text()
            total = len(current) + (len(PARAGRAPH_BREAK) if current else 0) + len(piece)
            if total > MAX_TEXT_LEN:
                return TextCapture(
                    False,
                    f"Ese mensaje no cabe: el libro tendría {total} de {MAX_TEXT_LEN} caracteres. "
                    f"Envía un trozo más corto o termina con /{FINISH}.",
                )
            draft.parts.append(piece)
            return TextCapture(True, f"Guardado. Llevas {total} de {MAX_TEXT_LEN} caracteres.")

    def _start(self, requester: Requester, argument: str) -> FeatureResult:
        if self.bans.is_banned(requester.key):
            return _reply(BANNED_REPLY)
        try:
            title = clean_title(argument)
        except PlayerBookError as exc:
            return _reply(str(exc))
        problem = self.library.problem()
        if problem:
            return _reply(problem)
        if self.library.exists(title):
            return _reply(f"Ya hay un libro titulado «{title}». Elige otro título.")
        with self._lock:
            current = self._drafts.get(requester.key)
            if current is not None:
                return _reply(
                    f"Ya estás escribiendo «{current.title}». "
                    f"Termínalo con /{FINISH} o descártalo con /{CANCEL}."
                )
            self._drafts[requester.key] = Draft(title=title, author=requester.name)
        instructions = (
            f"Escribiendo «{title}».\n"
            "Envíame aquí el texto, en uno o varios mensajes; cada mensaje es un párrafo. "
            "Marcaré con ✅ los que guarde. También vale un archivo .txt.\n"
            f"Máximo {MAX_TEXT_LEN} caracteres. Cuando acabes, usa /{FINISH} y elige la categoría. "
            f"Para descartarlo, /{CANCEL}."
        )
        return FeatureResult(
            ok=True,
            text=instructions,
            announce=False,
            ephemeral=True,
            private=True,
            embed_description=f"Empieza «{title}». Te he escrito por mensaje privado: envíame allí el texto.",
            private_messages=(instructions,),
        )

    def _finish(self, requester: Requester, argument: str) -> FeatureResult:
        with self._lock:
            draft = self._drafts.get(requester.key)
            text = draft.text() if draft else ""
        if self.bans.is_banned(requester.key):
            return _reply(BANNED_REPLY)
        if draft is None:
            return _reply(f"No estás escribiendo ningún libro. Empieza con /{START}.")
        if not text:
            return _reply(f"Todavía no me has enviado texto. Escríbeme por privado y vuelve a usar /{FINISH}.")
        category = _category(argument)
        if category is None:
            return _reply(f"Elige una categoría: {', '.join(CATEGORIES)}.")
        try:
            book = self.library.save(draft.title, draft.author, requester.key, text, category)
        except PlayerBookError as exc:
            return _reply(f"No se pudo guardar: {exc}")
        with self._lock:
            if self._drafts.get(requester.key) is draft:
                del self._drafts[requester.key]
        return FeatureResult(
            ok=True,
            text=(
                f"Guardado «{book.title}» en Libros de jugadores ({category}, {len(text)} caracteres). "
                "Ya sale en /biblioteca; en el juego aparecerá a más tardar en la próxima ronda."
            ),
            announce=False,
            ephemeral=True,
        )

    def _cancel(self, requester: Requester) -> FeatureResult:
        with self._lock:
            draft = self._drafts.pop(requester.key, None)
        if draft is None:
            return _reply("No estás escribiendo ningún libro.")
        return FeatureResult(ok=True, text=f"Descartado «{draft.title}».", announce=False, ephemeral=True)

    def _ban(self, config: Config | None, requester: Requester, argument: str) -> FeatureResult:
        user_id = _user_id(argument)
        if user_id is None:
            return _reply("Indica a quién: elige un usuario, o pon su id de Discord.")
        if config is not None and user_id in config.permissions.admin_ids:
            return _reply(f"<@{user_id}> es administrador del bot. Primero quítalo de [administradores] en permisos.txt.")
        key = _user_key(user_id)
        try:
            added = self.bans.ban(key, by=f"{requester.name} ({requester.key})")
        except OSError as exc:
            return _reply(f"No se pudo guardar la lista de baneados: {exc}")
        if not added:
            return _reply(f"<@{user_id}> ya tenía prohibido añadir libros.")
        with self._lock:
            draft = self._drafts.pop(key, None)
        discarded = f" Se ha descartado el libro que estaba escribiendo, «{draft.title}»." if draft else ""
        return FeatureResult(
            ok=True,
            text=f"<@{user_id}> ya no puede añadir libros.{discarded} Sus libros publicados siguen en la biblioteca.",
            announce=False,
            ephemeral=True,
        )

    def _unban(self, argument: str) -> FeatureResult:
        user_id = _user_id(argument)
        if user_id is None:
            return _reply("Indica a quién: elige un usuario, o pon su id de Discord.")
        try:
            removed = self.bans.unban(_user_key(user_id))
        except OSError as exc:
            return _reply(f"No se pudo guardar la lista de baneados: {exc}")
        if not removed:
            return _reply(f"<@{user_id}> no estaba baneado.")
        return FeatureResult(
            ok=True, text=f"<@{user_id}> vuelve a poder añadir libros.", announce=False, ephemeral=True
        )

    def _list_bans(self) -> FeatureResult:
        bans = self.bans.all()
        if not bans:
            return FeatureResult(
                ok=True, text="Nadie tiene prohibido añadir libros.", announce=False, ephemeral=True
            )
        lines = [f"Tienen prohibido añadir libros ({len(bans)}):"]
        for ban in bans:
            user_id = ban.key.removeprefix("discord:")
            lines.append(f"- <@{user_id}> (id {user_id}), por {ban.by} el {ban.when}")
        return FeatureResult(ok=True, text="\n".join(lines), announce=False, ephemeral=True)


def _user_id(argument: str) -> int | None:
    match = _DISCORD_USER.fullmatch(argument.strip())
    if match is None:
        return None
    value = int(match.group(1))
    return value if value > 0 else None


def _user_key(user_id: int) -> str:
    return f"discord:{user_id}"


def _category(argument: str) -> str | None:
    wanted = argument.strip().casefold()
    return next((category for category in CATEGORIES if category.casefold() == wanted), None)


def _reply(text: str) -> FeatureResult:
    return FeatureResult(ok=False, text=text, announce=False, ephemeral=True)
