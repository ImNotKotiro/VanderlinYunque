"""Acceso al servidor de juego. Las funciones del bot hablan con esta capa, no con el socket."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from byond import ByondError, ByondTopicClient
from config import Config, ConfigError
from snapshot import ServerSnapshot, snapshot_from_payload

# status no pide la clave. format=json lo devuelve world/Topic si COMMS_KEY existe en el servidor.
STATUS_QUERY = "status&format=json"

DEMO_STATUS = {
    "version": "demo",
    "mode": "Storytellers",
    "players": 17,
    "map_name": "Vanderlin",
    "gamestate": 3,
    "round_duration": 4980,
}


class ServerGateway(ABC):
    """Contrato para hablar con el servidor.

    Una funcion nueva que necesite otros datos debe añadir aqui un metodo
    e implementarlo en el gateway real y en el de demo.
    """

    @abstractmethod
    def player_snapshot(self) -> ServerSnapshot:
        raise NotImplementedError


class LiveServerGateway(ServerGateway):
    def __init__(self, client: ByondTopicClient) -> None:
        self.client = client

    def player_snapshot(self) -> ServerSnapshot:
        try:
            value = self.client.query(STATUS_QUERY)
        except ByondError as exc:
            return ServerSnapshot.offline(str(exc))
        if value.kind != "string" or value.text is None:
            return ServerSnapshot.offline("El servidor no devolvió el estado en texto.")
        return snapshot_from_payload(value.text)


class DemoServerGateway(ServerGateway):
    """Datos fijos para probar consola, comandos y formato sin red."""

    def player_snapshot(self) -> ServerSnapshot:
        return snapshot_from_payload(_demo_json())


def _demo_json() -> str:
    return json.dumps(DEMO_STATUS)


def build_gateway(config: Config) -> ServerGateway:
    if config.demo:
        return DemoServerGateway()
    if not config.byond_host or not config.byond_port:
        raise ConfigError(
            "Faltan BYOND_HOST y BYOND_PORT. "
            "Definelos en .env o usa --demo para probar sin el servidor."
        )
    client = ByondTopicClient(config.byond_host, config.byond_port, config.byond_timeout)
    return LiveServerGateway(client)
