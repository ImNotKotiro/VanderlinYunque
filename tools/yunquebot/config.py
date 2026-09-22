"""Configuracion del bot, leida de variables de entorno y de un .env local."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
ENV_PATH = TOOL_ROOT / ".env"


class ConfigError(Exception):
    """La configuracion esta incompleta o tiene un valor invalido."""


@dataclass(frozen=True)
class Config:
    byond_host: str
    byond_port: int
    byond_timeout: float
    server_name: str
    update_interval_seconds: int
    min_players_to_announce: int
    discord_token: str
    discord_channel_id: int | None
    discord_guild_id: int | None
    demo: bool


def parse_dotenv(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.is_file():
        return
    try:
        parsed = parse_dotenv(path.read_text(encoding="utf-8"))
    except UnicodeError as exc:
        raise ConfigError(f"No se pudo leer {path.name}: {exc}") from exc
    for key, value in parsed.items():
        os.environ.setdefault(key, value)


def load_config(
    source: Mapping[str, str],
    *,
    host: str | None = None,
    port: int | None = None,
    demo: bool = False,
) -> Config:
    byond_host = (host if host is not None else _raw(source, "BYOND_HOST")).strip()
    byond_port = port if port is not None else _int(source, "BYOND_PORT", 0)
    if byond_port and not 1 <= byond_port <= 65535:
        raise ConfigError("BYOND_PORT tiene que estar entre 1 y 65535.")

    timeout = _float(source, "BYOND_TIMEOUT", 5.0)
    if timeout <= 0:
        raise ConfigError("BYOND_TIMEOUT tiene que ser mayor que 0.")

    interval = _int(source, "UPDATE_INTERVAL_SECONDS", 900)
    if interval < 0 or 0 < interval < 15:
        raise ConfigError(
            "UPDATE_INTERVAL_SECONDS tiene que ser 0 (solo comandos) o 15 segundos o mas. "
            "El valor previsto es 900 (15 minutos)."
        )

    server_name = _raw(source, "SERVER_NAME") or "Yunque"
    minimum = _int(source, "MIN_PLAYERS_TO_ANNOUNCE", 5)
    if minimum < -1:
        raise ConfigError(
            "MIN_PLAYERS_TO_ANNOUNCE tiene que ser -1 o mayor. "
            "El aviso automático solo sale si hay más jugadores que ese número."
        )

    return Config(
        byond_host=byond_host,
        byond_port=byond_port,
        byond_timeout=timeout,
        server_name=server_name,
        update_interval_seconds=interval,
        min_players_to_announce=minimum,
        discord_token=_raw(source, "DISCORD_TOKEN"),
        discord_channel_id=_optional_int(source, "DISCORD_CHANNEL_ID"),
        discord_guild_id=_optional_int(source, "DISCORD_GUILD_ID"),
        demo=demo,
    )


def _raw(source: Mapping[str, str], key: str) -> str:
    value = source.get(key, "")
    if value is None:
        return ""
    return str(value).strip()


def _int(source: Mapping[str, str], key: str, default: int) -> int:
    raw = _raw(source, key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} debe ser un número entero.") from exc


def _optional_int(source: Mapping[str, str], key: str) -> int | None:
    raw = _raw(source, key)
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} debe ser un número entero.") from exc
    if value <= 0:
        raise ConfigError(f"{key} tiene que ser un id positivo.")
    return value


def _float(source: Mapping[str, str], key: str, default: float) -> float:
    raw = _raw(source, key)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} debe ser un número.") from exc
