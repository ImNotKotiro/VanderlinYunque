"""Consola para probar el bot sin Discord."""

from __future__ import annotations

import time
from dataclasses import replace

from bot.app import App
from bot.config import ConfigError
from bot.features.base import CONSOLE_REQUESTER
from bot.formatting import format_interval
from bot.server.gateway import DemoServerGateway, LiveServerGateway, build_gateway

HELP = """Comandos de consola:
  estado               Consulta el conteo (en Discord es /estado)
  biblioteca <listado> Lista libros: codigo, trabajos o jugadores
  libro <título>       Muestra un libro del código o de jugadores (en Discord llega por privado)
  escribir_libro <título> | <autor>  Empieza un libro de jugador; las líneas siguientes son su texto
  terminar_libro <categoría>  Lo guarda: Apocrypha & Grimoires, Myths & Tales, Legends & Accounts, Thesis o Eoratica
  cancelar_libro              Descarta el libro que estás escribiendo
  banear_escritor <id>        Prohíbe añadir libros a ese usuario de Discord (admin en Discord)
  desbanear_escritor <id>     Le deja volver a añadir libros (admin en Discord)
  escritores_baneados         Lista los baneados (admin en Discord)
  agenda               Muestra cada cuánto se publicaría el aviso
  fuente               Dice si los datos son de ejemplo o del servidor
  demo on              Usa datos de ejemplo, sin red
  demo off             Vuelve a consultar el servidor configurado
  ayuda                Muestra esta ayuda
  salir                Cierra la consola
"""


def describe_source(app: App) -> str:
    gateway = app.gateway
    if isinstance(gateway, DemoServerGateway):
        return "Fuente: datos de ejemplo (demo), sin conectar al servidor."
    if isinstance(gateway, LiveServerGateway):
        return f"Fuente: servidor {gateway.client.host}:{gateway.client.port}"
    return "Fuente: desconocida."


def format_schedule(app: App, now: float) -> str:
    lines = ["Avisos periódicos:"]
    periodic = False
    for feature in app.features:
        interval = feature.interval_seconds
        if not interval:
            continue
        periodic = True
        name = feature.command_names[0]
        every = format_interval(interval)
        last = app.last_run(feature.id)
        if last is None:
            lines.append(f"  {name}: cada {every}. Todavía no se ha publicado.")
        else:
            remaining = max(0, int(interval - (now - last)))
            lines.append(f"  {name}: cada {every}. Faltan {remaining} s.")
    if not periodic:
        lines.append("  Ninguno. El intervalo está en 0; solo responden los comandos.")
    lines.append("Comandos: " + ", ".join(app.command_names()))
    return "\n".join(lines)


def execute_console_line(app: App, line: str, now: float = 0.0) -> str | None:
    """Ejecuta una linea. None significa salir."""
    parts = line.strip().split()
    if not parts:
        return ""
    command = parts[0].lower()
    if command in {"salir", "exit", "quit"}:
        return None
    if command in {"ayuda", "help", "?"}:
        return HELP
    if command == "fuente":
        return describe_source(app)
    if command == "agenda":
        return format_schedule(app, now)
    if command == "demo":
        return _switch_demo(app, parts[1] if len(parts) > 1 else "")
    if app.feature_for(command) is None:
        capture = app.capture_text(CONSOLE_REQUESTER, line)
        if capture is not None:
            return capture.reply
    argument = " ".join(parts[1:])
    extra = ""
    feature = app.feature_for(command)
    if feature is not None and feature.command_extra_argument(command):
        argument, _, extra = argument.partition("|")
    result = app.run_command(command, argument.strip(), CONSOLE_REQUESTER, extra.strip())
    return result.text


def _switch_demo(app: App, mode: str) -> str:
    mode = mode.lower()
    if mode in {"on", "1", "si", "sí"}:
        app.gateway = DemoServerGateway()
        return "Usando datos de ejemplo. No se contacta al servidor."
    if mode in {"off", "0", "no"}:
        try:
            app.gateway = build_gateway(replace(app.config, demo=False))
        except ConfigError as exc:
            return f"Error: {exc}"
        return describe_source(app)
    return "Usa 'demo on' o 'demo off'."


def run_console(app: App) -> int:
    print(f"YunqueBot, consola. Servidor: {app.config.server_name}.")
    print(describe_source(app))
    print("Escribe 'ayuda' para ver los comandos. Discord no hace falta.")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        output = execute_console_line(app, line, now=time.monotonic())
        if output is None:
            return 0
        if output:
            print(output)
