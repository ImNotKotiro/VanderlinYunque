"""Recuerda el último aviso automático para poder sustituirlo."""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger("yunquebot")


def message_belongs_to_bot(author_id: int, bot_id: int | None) -> bool:
    """Solo el mensaje propio del bot se puede borrar."""
    return bot_id is not None and author_id == bot_id


class AnnouncementLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._ids: dict[str, int] = {}

    def load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            log.warning("No se pudo leer %s. Se empieza sin aviso anterior.", self.path.name)
            return
        if not isinstance(raw, dict):
            return
        loaded: dict[str, int] = {}
        for key, value in raw.items():
            try:
                loaded[str(key)] = int(value)
            except (TypeError, ValueError):
                continue
        self._ids = loaded

    def get(self, feature_id: str) -> int | None:
        return self._ids.get(feature_id)

    def remember(self, feature_id: str, message_id: int) -> None:
        self._ids[feature_id] = message_id
        try:
            self.path.write_text(json.dumps(self._ids), encoding="utf-8")
        except OSError:
            log.warning("No se pudo guardar el id del aviso en %s.", self.path.name)
