"""Conteo de jugadores conectados al servidor."""

from __future__ import annotations

from config import Config
from features.base import Feature, FeatureResult
from formatting import embed_color, embed_description, embed_fields, embed_title, format_player_report
from gateway import ServerGateway
from snapshot import ServerSnapshot


class PlayerCountFeature(Feature):
    id = "player_count"
    command_names = ("jugadores", "players")
    description = "Muestra cuántos jugadores hay conectados al servidor."

    def __init__(self, config: Config) -> None:
        seconds = config.update_interval_seconds
        self.interval_seconds = seconds if seconds > 0 else None

    def run(self, gateway: ServerGateway, config: Config) -> FeatureResult:
        snapshot = gateway.player_snapshot()
        return FeatureResult(
            ok=snapshot.online,
            text=format_player_report(snapshot, config.server_name),
            announce=should_announce(snapshot, config.min_players_to_announce),
            embed_title=embed_title(config.server_name),
            embed_description=embed_description(snapshot),
            embed_color=embed_color(snapshot),
            embed_fields=embed_fields(snapshot),
            embed_footer="Consulta con /jugadores",
        )


def should_announce(snapshot: ServerSnapshot, minimum: int) -> bool:
    """El aviso periódico solo sale si hay más jugadores que `minimum`."""
    if not snapshot.online or snapshot.players is None:
        return False
    return snapshot.players > minimum
