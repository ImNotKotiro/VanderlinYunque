"""Contrato de una funcion del bot.

Para añadir una funcion:
1. Crea un archivo en bot/features/.
2. Hereda de Feature e implementa run().
3. Registra la clase en build_features().

La consola y Discord descubren solas los comandos y el intervalo.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bot.config import Config
from bot.server.gateway import ServerGateway

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
    #: Con `private`, mensajes que se envían uno tras otro en lugar de un archivo.
    private_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Requester:
    """Quién hace la petición.

    `key` es estable: en Discord, discord:<id de usuario>. `name` es el nombre que se ve;
    `account`, el nombre de usuario de Discord (@nombre), que no lleva espacios.
    """

    key: str
    name: str
    account: str = ""


CONSOLE_REQUESTER = Requester(key="consola", name="Consola", account="consola")


@dataclass(frozen=True)
class TextCapture:
    """Respuesta a un texto suelto. Sin `accepted`, `reply` explica por qué no se guardó."""

    accepted: bool
    reply: str


class Feature(ABC):
    id: str
    command_names: tuple[str, ...]
    description: str
    #: None: solo por comando. Un entero: tambien se publica cada tantos segundos.
    interval_seconds: int | None = None
    #: Comandos solo para administradores aunque no estén en [comandos_admin]. La consola no los limita.
    admin_command_names: tuple[str, ...] = ()

    def command_description(self, name: str) -> str:
        return self.description

    def command_argument(self, name: str) -> str | None:
        """Nombre del argumento de texto del comando, si lleva uno."""
        return None

    def command_extra_argument(self, name: str) -> str | None:
        """Nombre de un segundo argumento de texto, opcional. En la consola va detrás de |."""
        return None

    def command_extra_argument_description(self, name: str) -> str:
        return ""

    def command_argument_is_user(self, name: str) -> bool:
        """En Discord se elige un usuario; run() recibe su id. En la consola vale el id o <@id>."""
        return False

    def command_argument_description(self, name: str) -> str:
        return ""

    def command_choices(self, name: str) -> tuple[tuple[str, str], ...]:
        """Pares (valor, etiqueta). Si hay alguno, el argumento solo admite esos valores."""
        return ()

    def reply_is_ephemeral(self, name: str) -> bool:
        return False

    @abstractmethod
    def run(
        self,
        gateway: ServerGateway,
        config: Config,
        command: str = "",
        argument: str = "",
        requester: Requester | None = None,
        extra: str = "",
    ) -> FeatureResult:
        """Puede bloquear. Discord la ejecuta en un hilo. `extra` es el argumento opcional, si lo hay."""
        raise NotImplementedError

    def capture_text(self, requester: Requester, text: str) -> TextCapture | None:
        """Texto que no es un comando: mensajes privados en Discord, líneas sueltas en la consola.

        None si a esta función no le interesa. Se llama desde el hilo de Discord: no debe bloquear.
        """
        return None


def validate_features(features: list[Feature]) -> None:
    seen_ids: set[str] = set()
    seen_names: dict[str, str] = {}
    for feature in features:
        if not feature.id or feature.id in seen_ids:
            raise RuntimeError(f"Funcion duplicada o sin id: {feature.id!r}.")
        seen_ids.add(feature.id)
        if not feature.command_names:
            raise RuntimeError(f"{feature.id} no tiene comandos.")
        stray = set(feature.admin_command_names) - set(feature.command_names)
        if stray:
            raise RuntimeError(f"{feature.id}: {', '.join(sorted(stray))} es de administrador pero no es un comando.")
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
