"""Contrato de una funcion del bot.

Para añadir una funcion:
1. Crea un archivo en features/.
2. Hereda de Feature e implementa run().
3. Registra la clase en build_features().

La consola y Discord descubren solas los comandos y el intervalo.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from config import Config
from gateway import ServerGateway

_COMMAND_NAME = re.compile(r"[a-z0-9_-]{1,32}")


@dataclass(frozen=True)
class FeatureResult:
    """Resultado de una funcion.

    `text` es el mensaje de la consola. Discord usa el embed si trae titulo.
    `announce` en falso omite solo el aviso automatico; el comando sigue respondiendo.
    """

    ok: bool
    text: str
    announce: bool = True
    embed_title: str = ""
    embed_description: str = ""
    embed_color: int | None = None
    embed_fields: tuple[tuple[str, str], ...] = ()
    embed_footer: str = ""
    ephemeral: bool = False
    private: bool = False
    attachment_name: str = ""
    attachment_text: str = ""


class Feature(ABC):
    id: str
    command_names: tuple[str, ...]
    description: str
    #: None: solo por comando. Un entero: tambien se publica cada tantos segundos.
    interval_seconds: int | None = None

    def command_description(self, name: str) -> str:
        return self.description

    def command_argument(self, name: str) -> str | None:
        """Nombre del argumento de texto del comando, si lleva uno."""
        return None

    def reply_is_ephemeral(self, name: str) -> bool:
        return False

    @abstractmethod
    def run(
        self,
        gateway: ServerGateway,
        config: Config,
        command: str = "",
        argument: str = "",
    ) -> FeatureResult:
        """Puede bloquear. Discord la ejecuta en un hilo."""
        raise NotImplementedError


def validate_features(features: list[Feature]) -> None:
    seen_ids: set[str] = set()
    seen_names: dict[str, str] = {}
    for feature in features:
        if not feature.id or feature.id in seen_ids:
            raise RuntimeError(f"Funcion duplicada o sin id: {feature.id!r}.")
        seen_ids.add(feature.id)
        if not feature.command_names:
            raise RuntimeError(f"{feature.id} no tiene comandos.")
        if not feature.description or len(feature.description) > 100:
            raise RuntimeError(f"{feature.id} necesita una descripcion de 1 a 100 caracteres.")
        for name in feature.command_names:
            if _COMMAND_NAME.fullmatch(name) is None:
                raise RuntimeError(
                    f"Nombre de comando invalido en {feature.id}: {name!r}. "
                    "Usa minusculas, numeros, _ o -."
                )
            owner = seen_names.get(name)
            if owner:
                raise RuntimeError(f"El comando {name} esta repetido en {owner} y {feature.id}.")
            seen_names[name] = feature.id
