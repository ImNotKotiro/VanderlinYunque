"""Usuarios que no pueden añadir libros. Se guarda en datos/ para que dure entre reinicios."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bot.config import ConfigError


@dataclass(frozen=True)
class WriterBan:
    key: str
    by: str
    when: str


class WriterBans:
    """Sin `path`, la lista solo vive en memoria."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._bans: dict[str, WriterBan] = {}
        self._lock = threading.Lock()
        self._load()

    def is_banned(self, key: str) -> bool:
        with self._lock:
            return key in self._bans

    def all(self) -> list[WriterBan]:
        with self._lock:
            return sorted(self._bans.values(), key=lambda ban: ban.when)

    def ban(self, key: str, by: str, when: datetime | None = None) -> bool:
        """False si ya estaba baneado. Lanza OSError si no se puede guardar."""
        stamp = (when or datetime.now()).strftime("%Y-%m-%d %H:%M")
        with self._lock:
            if key in self._bans:
                return False
            updated = {**self._bans, key: WriterBan(key=key, by=by, when=stamp)}
            self._save(updated)
            self._bans = updated
            return True

    def unban(self, key: str) -> bool:
        """False si no estaba baneado. Lanza OSError si no se puede guardar."""
        with self._lock:
            if key not in self._bans:
                return False
            updated = {other: ban for other, ban in self._bans.items() if other != key}
            self._save(updated)
            self._bans = updated
            return True

    def _load(self) -> None:
        if self.path is None or not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._bans = {
                str(key): WriterBan(key=str(key), by=str(entry.get("por", "")), when=str(entry.get("fecha", "")))
                for key, entry in raw.items()
            }
        except (OSError, ValueError, AttributeError) as exc:
            raise ConfigError(
                f"No se pudo leer {self.path.name}: {exc}. Arréglalo o bórralo para empezar sin baneados."
            ) from exc

    def _save(self, bans: dict[str, WriterBan]) -> None:
        if self.path is None:
            return
        payload = {key: {"por": ban.by, "fecha": ban.when} for key, ban in bans.items()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        try:
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
