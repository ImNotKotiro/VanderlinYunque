"""Lectura de la respuesta ?status del servidor."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import parse_qs

GAME_STATE_PLAYING = 3

GAME_STATE_LABELS = {
    0: "Iniciando",
    1: "En lobby",
    2: "Preparando la ronda",
    3: "En juego",
    4: "Ronda terminada",
}

_SERVER_ERRORS = {
    "Commskey disabled": (
        "El servidor tiene COMMS_KEY vacía y rechaza las consultas. "
        "Hay que definirla en config/comms.txt del juego. El bot no usa esa clave."
    ),
    "Configuration has not initialised yet": "El servidor todavía está arrancando.",
    "Bad Key": "El servidor rechazó la clave de comunicaciones.",
}


@dataclass(frozen=True)
class ServerSnapshot:
    online: bool
    players: int | None = None
    map_name: str | None = None
    game_state: int | None = None
    round_duration_seconds: int | None = None
    error: str | None = None

    @staticmethod
    def offline(error: str) -> ServerSnapshot:
        return ServerSnapshot(online=False, error=error)

    @property
    def game_state_label(self) -> str | None:
        if self.game_state is None:
            return None
        return GAME_STATE_LABELS.get(self.game_state, str(self.game_state))


def explain_server_error(message: str) -> str:
    cleaned = message.strip()
    return _SERVER_ERRORS.get(cleaned, cleaned or "El servidor respondió vacío.")


def snapshot_from_payload(text: str) -> ServerSnapshot:
    cleaned = text.strip().strip("\x00")
    if not cleaned:
        return ServerSnapshot.offline("El servidor respondió vacío.")
    if cleaned[0] in "{[\"":
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return ServerSnapshot.offline("La respuesta JSON no se pudo leer.")
        if isinstance(parsed, str):
            return ServerSnapshot.offline(explain_server_error(parsed))
        if isinstance(parsed, dict):
            return snapshot_from_mapping(parsed)
        return ServerSnapshot.offline("La respuesta JSON no es un objeto.")
    if "=" in cleaned:
        parsed = parse_qs(cleaned, keep_blank_values=True)
        flat = {key: values[0] if values else "" for key, values in parsed.items()}
        return snapshot_from_mapping(flat)
    return ServerSnapshot.offline(explain_server_error(cleaned))


def snapshot_from_mapping(data: Mapping[str, object]) -> ServerSnapshot:
    if "players" not in data or data.get("players") in (None, ""):
        return ServerSnapshot.offline("La respuesta no incluye el número de jugadores.")
    try:
        players = int(round(float(data["players"])))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ServerSnapshot.offline("El número de jugadores no es válido.")
    if players < 0:
        return ServerSnapshot.offline("El número de jugadores no es válido.")
    return ServerSnapshot(
        online=True,
        players=players,
        map_name=_optional_text(data.get("map_name")),
        game_state=_optional_int(data.get("gamestate")),
        round_duration_seconds=_optional_int(data.get("round_duration")),
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null":
        return None
    return text


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null":
        return None
    try:
        return int(round(float(text)))
    except (TypeError, ValueError):
        return None
