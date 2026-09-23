"""Nucleo del bot, independiente de Discord y de la consola."""

from __future__ import annotations

from config import Config
from features import build_features
from features.base import Feature, FeatureResult
from gateway import ServerGateway


class App:
    def __init__(
        self,
        config: Config,
        gateway: ServerGateway,
        features: list[Feature] | None = None,
    ) -> None:
        self.config = config
        self.gateway = gateway
        self.features = features if features is not None else build_features(config)
        self._last_run: dict[str, float] = {}

    def feature_for(self, command: str) -> Feature | None:
        key = command.strip().lower()
        for feature in self.features:
            if key in feature.command_names:
                return feature
        return None

    def command_names(self) -> list[str]:
        names: list[str] = []
        for feature in self.features:
            names.extend(feature.command_names)
        return names

    def run_command(self, command: str, argument: str = "") -> FeatureResult:
        feature = self.feature_for(command)
        if feature is None:
            known = ", ".join(self.command_names()) or "(ninguno)"
            return FeatureResult(ok=False, text=f"Comando desconocido. Comandos: {known}")
        return feature.run(self.gateway, self.config, command, argument)

    def due_features(self, now: float) -> list[Feature]:
        due: list[Feature] = []
        for feature in self.features:
            interval = feature.interval_seconds
            if not interval:
                continue
            last = self._last_run.get(feature.id)
            if last is None or (now - last) >= interval:
                due.append(feature)
        return due

    def mark_ran(self, feature: Feature, now: float) -> None:
        self._last_run[feature.id] = now

    def last_run(self, feature_id: str) -> float | None:
        return self._last_run.get(feature_id)

    def seconds_until_next(self, now: float) -> float:
        waits: list[float] = []
        for feature in self.features:
            interval = feature.interval_seconds
            if not interval:
                continue
            last = self._last_run.get(feature.id)
            if last is None:
                waits.append(0.0)
            else:
                waits.append(max(0.0, interval - (now - last)))
        if not waits:
            return 60.0
        return min(waits)
