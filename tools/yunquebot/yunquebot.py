"""Punto de entrada de YunqueBot.

Consola y comprobaciones no necesitan Discord.
El modo discord es el unico que usa el token.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from bot.config import (
    ENV_PATH,
    PERMISSIONS_PATH,
    ConfigError,
    load_config,
    load_dotenv,
    load_permissions,
)


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 10):
        print("YunqueBot necesita Python 3.10 o superior.", file=sys.stderr)
        return 1
    _configure_stdio()

    parser = argparse.ArgumentParser(
        prog="yunquebot",
        description="Consulta los jugadores del servidor y puede publicarlos en Discord.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    console = sub.add_parser("console", help="Consola interactiva, sin Discord.")
    run = sub.add_parser("run", help="Ejecuta un comando una vez y termina.")
    run.add_argument("name", help="Por ejemplo: estado")
    sub.add_parser("selftest", help="Comprueba el bot sin red y sin Discord.")
    discord_mode = sub.add_parser("discord", help="Arranca el bot de Discord.")

    for item in (console, run, discord_mode):
        item.add_argument("--demo", action="store_true", help="Usa datos de ejemplo, sin servidor.")
        item.add_argument("--host", help="Host de DreamDaemon. Pisa BYOND_HOST.")
        item.add_argument("--port", type=int, help="Puerto de DreamDaemon. Pisa BYOND_PORT.")

    args = parser.parse_args(argv)
    if args.mode == "selftest":
        return _selftest()

    try:
        load_dotenv(ENV_PATH)
        app = _build_app(args)
        if args.mode == "console":
            from bot.interfaces.console import run_console

            return run_console(app)
        if args.mode == "run":
            result = app.run_command(args.name)
            print(result.text)
            return 0 if result.ok else 1
        if args.mode == "discord":
            _configure_logging()
            try:
                from bot.interfaces.discord_bot import run_discord
            except ImportError:
                print(
                    "Error: falta discord.py. Instálalo con: pip install -r requirements.txt",
                    file=sys.stderr,
                )
                return 2

            logging.getLogger("yunquebot").info("Iniciando YunqueBot...")
            run_discord(app)
            return 0
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print()
        return 0
    return 2


def _build_app(args: argparse.Namespace):
    from bot.app import App
    from bot.server.gateway import build_gateway

    config = load_config(
        os.environ,
        host=args.host,
        port=args.port,
        demo=args.demo,
        permissions=load_permissions(PERMISSIONS_PATH),
    )
    return App(config, build_gateway(config))


def _selftest() -> int:
    import unittest

    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_yunquebot")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


class _ConsoleFormatter(logging.Formatter):
    """Solo los avisos y errores llevan etiqueta; el resto es el estado del bot."""

    LABELS = {logging.WARNING: "AVISO: ", logging.ERROR: "ERROR: ", logging.CRITICAL: "ERROR: "}

    def format(self, record: logging.LogRecord) -> str:
        record.label = self.LABELS.get(record.levelno, "")
        return super().format(record)


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        _ConsoleFormatter("[%(asctime)s] %(label)s%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    logging.getLogger("yunquebot").setLevel(logging.INFO)
    logging.getLogger("discord").setLevel(logging.ERROR)


if __name__ == "__main__":
    sys.exit(main())
