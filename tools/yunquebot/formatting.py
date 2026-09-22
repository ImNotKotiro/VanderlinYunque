"""Textos que comparten la consola y Discord."""

from __future__ import annotations

from snapshot import GAME_STATE_PLAYING, ServerSnapshot

RULE = "━━━━━━━━━━━━━━━━━━━━"
COLOR_OFFLINE = 0x8C3A3A
COLOR_PLAYING = 0xC6A15B
COLOR_WAITING = 0x3E5C4C


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
    title = f"✦ **{server_name}** ✦"
    if not snapshot.online or snapshot.players is None:
        detail = snapshot.error or "Sin detalle."
        return "\n".join(
            [
                title,
                RULE,
                "No se pudo consultar el servidor.",
                detail,
                RULE,
            ]
        )

    lines = [title, RULE, _count_line(snapshot.players)]
    details = _detail_lines(snapshot)
    if details:
        lines.append("")
        lines.extend(details)
    lines.append(RULE)
    return "\n".join(lines)


def embed_title(server_name: str) -> str:
    return f"✦ {server_name} ✦"


def embed_description(snapshot: ServerSnapshot) -> str:
    if not snapshot.online or snapshot.players is None:
        detail = snapshot.error or "Sin detalle."
        return f"No se pudo consultar el servidor.\n{detail}"
    return _count_line(snapshot.players)


def embed_color(snapshot: ServerSnapshot) -> int:
    if not snapshot.online or snapshot.players is None:
        return COLOR_OFFLINE
    if snapshot.game_state == GAME_STATE_PLAYING:
        return COLOR_PLAYING
    return COLOR_WAITING


def embed_fields(snapshot: ServerSnapshot) -> tuple[tuple[str, str], ...]:
    if not snapshot.online or snapshot.players is None:
        return ()
    fields: list[tuple[str, str]] = []
    if snapshot.map_name:
        fields.append(("🗺️ Mapa", snapshot.map_name))
    if snapshot.game_state_label:
        fields.append(("🕯️ Estado", snapshot.game_state_label))
    if snapshot.game_state == GAME_STATE_PLAYING and snapshot.round_duration_seconds is not None:
        fields.append(("⏳ Duración", format_duration(snapshot.round_duration_seconds)))
    return tuple(fields)


def _count_line(players: int) -> str:
    if players == 1:
        return "**1** jugador conectado"
    return f"**{players}** jugadores conectados"


def _detail_lines(snapshot: ServerSnapshot) -> list[str]:
    lines: list[str] = []
    if snapshot.map_name:
        lines.append(f"🗺️ **Mapa** · {snapshot.map_name}")
    if snapshot.game_state_label:
        lines.append(f"🕯️ **Estado** · {snapshot.game_state_label}")
    if snapshot.game_state == GAME_STATE_PLAYING and snapshot.round_duration_seconds is not None:
        lines.append(f"⏳ **Duración** · {format_duration(snapshot.round_duration_seconds)}")
    return lines
