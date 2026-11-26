"""Registro de las peticiones al bot: un fichero por comando en logs/. Solo se añade, nunca se vacía."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

log = logging.getLogger("yunquebot")
_UNSAFE = re.compile(r"[^a-z0-9_-]")


@dataclass(frozen=True)
class Request:
    command: str
    user: str
    place: str
    arguments: Mapping[str, str] = field(default_factory=dict)


class RequestLog:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def path_for(self, command: str) -> Path:
        name = _UNSAFE.sub("_", command.strip().lower()) or "desconocido"
        return self.folder / f"{name}.txt"

    def record(
        self,
        request: Request,
        outcome: str,
        response: str,
        when: datetime | None = None,
    ) -> None:
        moment = (when or datetime.now().astimezone()).strftime("%Y-%m-%d %H:%M:%S %z")
        arguments = ", ".join(f"{key} = {value}" for key, value in request.arguments.items())
        body = "\n".join(f"    {line}" for line in (response or "(vacía)").splitlines())
        entry = (
            f"[{moment}] {outcome}\n"
            f"Usuario: {request.user}\n"
            f"Lugar: {request.place}\n"
            f"Parámetros: {arguments or '(ninguno)'}\n"
            f"Respuesta:\n{body}\n\n"
        )
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            with self.path_for(request.command).open("a", encoding="utf-8") as handle:
                handle.write(entry)
        except OSError:
            log.exception("No se pudo escribir el log de /%s.", request.command)
