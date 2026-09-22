"""Textos que comparten la consola y Discord."""

from __future__ import annotations

from snapshot import GAME_STATE_PLAYING, ServerSnapshot


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours} h {minutes} min"
    if minutes:
        return f"{minutes} min"
    return f"{secs} s"


def format_interval(seconds: int) -> str:
    if seconds <= 0:
        return "desactivado"
    if seconds % 3600 == 0:
        hours = seconds // 3600
        return "1 hora" if hours == 1 else f"{hours} horas"
    if seconds % 60 == 0:
        minutes = seconds // 60
        return "1 minuto" if minutes == 1 else f"{minutes} minutos"
    return f"{seconds} segundos"


def format_player_report(snapshot: ServerSnapshot, server_name: str) -> str:
    if not snapshot.online or snapshot.players is None:
        detail = snapshot.error or "Sin detalle."
        return f"**{server_name}** — no se pudo consultar el servidor.\n{detail}"

    if snapshot.players == 1:
        lines = [f"**{server_name}** — 1 jugador conectado"]
    else:
        lines = [f"**{server_name}** — {snapshot.players} jugadores conectados"]

    if snapshot.map_name:
        lines.append(f"Mapa: {snapshot.map_name}")
    if snapshot.game_state_label:
        lines.append(f"Estado: {snapshot.game_state_label}")
    if snapshot.game_state == GAME_STATE_PLAYING and snapshot.round_duration_seconds is not None:
        lines.append(f"Duración: {format_duration(snapshot.round_duration_seconds)}")
    return "\n".join(lines)
