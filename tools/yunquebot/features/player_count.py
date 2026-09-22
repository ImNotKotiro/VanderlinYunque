"""Conteo de jugadores conectados al servidor."""

from __future__ import annotations

from config import Config
from features.base import Feature, FeatureResult
from formatting import format_player_report
from gateway import ServerGateway


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
        )
