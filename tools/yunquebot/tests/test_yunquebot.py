"""Comprueba el bot sin Discord y, salvo un socket local, sin red."""

from __future__ import annotations

import json
import socket
import struct
import threading
import unittest
from pathlib import Path

from announcements import AnnouncementLog, message_belongs_to_bot
from books import BookLibrary, html_fragment_to_text
from features.books import BooksFeature
from app import App
from byond import (
    ByondError,
    ByondTopicClient,
    TopicValue,
    decode_topic_response,
    encode_topic_query,
)
from config import ConfigError, load_config, parse_dotenv
from console import execute_console_line
from features import build_features
from features.player_count import PlayerCountFeature
from features.base import Feature, FeatureResult, validate_features
from formatting import format_player_report
from gateway import STATUS_QUERY, DemoServerGateway, LiveServerGateway, build_gateway
from snapshot import snapshot_from_payload


class EncodeTests(unittest.TestCase):
    def test_status_query_matches_topic_layout(self) -> None:
        query = "?status&format=json"
        packet = encode_topic_query("status&format=json")
        message = query.encode("ascii")
        self.assertEqual(packet[:2], b"\x00\x83")
        length = struct.unpack(">H", packet[2:4])[0]
        self.assertEqual(length, len(message) + 6)
        self.assertEqual(packet[4:9], b"\x00" * 5)
        self.assertEqual(packet[9:-1], message)
        self.assertEqual(packet[-1:], b"\x00")

    def test_decodes_string_and_float(self) -> None:
        text = decode_topic_response(_response(b"\x06" + b"hola\x00"))
        self.assertEqual(text, TopicValue(kind="string", text="hola"))

        number = decode_topic_response(_response(b"\x2a" + struct.pack(">f", 42.0)))
        self.assertEqual(number.kind, "number")
        self.assertEqual(round(number.number or 0), 42)

        self.assertEqual(decode_topic_response(_response(b"\x00")).kind, "null")
        with self.assertRaises(ByondError):
            decode_topic_response(_response(b"\x01"))


class SnapshotTests(unittest.TestCase):
    def test_json_status_and_message(self) -> None:
        snapshot = snapshot_from_payload(
            '{"players": 17, "map_name": "Vanderlin", "gamestate": 3, "round_duration": 4980}'
        )
        self.assertTrue(snapshot.online)
        self.assertEqual(snapshot.players, 17)
        self.assertEqual(
            format_player_report(snapshot, "Yunque"),
            "\n".join(
                [
                    "✦ **Yunque** ✦",
                    "━━━━━━━━━━━━━━━━━━━━",
                    "**17** jugadores conectados",
                    "",
                    "🗺️ **Mapa** · Vanderlin",
                    "🕯️ **Estado** · En juego",
                    "⏳ **Duración** · 1 h 23 min",
                    "━━━━━━━━━━━━━━━━━━━━",
                ]
            ),
        )

    def test_singular_and_empty_round(self) -> None:
        one = snapshot_from_payload('{"players": 1}')
        self.assertIn("**1** jugador conectado", format_player_report(one, "Yunque"))
        self.assertIn("✦ **Yunque** ✦", format_player_report(one, "Yunque"))
        zero = snapshot_from_payload('{"players": 0}')
        self.assertIn("**0** jugadores conectados", format_player_report(zero, "Yunque"))

    def test_params_and_known_errors(self) -> None:
        snapshot = snapshot_from_payload("players=8&map_name=My+Map&gamestate=1&round_duration=10")
        self.assertEqual(snapshot.players, 8)
        self.assertEqual(snapshot.map_name, "My Map")
        self.assertEqual(snapshot.game_state_label, "En lobby")
        text = format_player_report(snapshot, "Yunque")
        self.assertNotIn("Duración", text)

        disabled = snapshot_from_payload('"Commskey disabled"')
        self.assertFalse(disabled.online)
        self.assertIn("COMMS_KEY", disabled.error or "")

    def test_rejects_bad_counts(self) -> None:
        self.assertFalse(snapshot_from_payload('{"map_name": "X"}').online)
        self.assertFalse(snapshot_from_payload('{"players": -1}').online)
        self.assertFalse(snapshot_from_payload("").online)


class ConfigTests(unittest.TestCase):
    def test_defaults_and_dotenv(self) -> None:
        config = load_config({})
        self.assertEqual(config.server_name, "Yunque")
        self.assertEqual(config.update_interval_seconds, 900)
        self.assertEqual(config.min_players_to_announce, 5)
        self.assertFalse(config.demo)
        self.assertIsNone(config.discord_channel_id)

        parsed = parse_dotenv('# comentario\n\nDISCORD_TOKEN="abc"\nBYOND_PORT = 2500\n')
        self.assertEqual(parsed["DISCORD_TOKEN"], "abc")
        self.assertEqual(parsed["BYOND_PORT"], "2500")

    def test_interval_guard(self) -> None:
        with self.assertRaises(ConfigError):
            load_config({"UPDATE_INTERVAL_SECONDS": "10"})
        disabled = load_config({"UPDATE_INTERVAL_SECONDS": "0"})
        self.assertEqual(disabled.update_interval_seconds, 0)
        self.assertIsNone(build_features(disabled)[0].interval_seconds)

    def test_demo_gateway_does_not_need_a_server(self) -> None:
        config = load_config({}, demo=True)
        app = App(config, build_gateway(config))
        self.assertIsInstance(app.gateway, DemoServerGateway)
        result = app.run_command("estado")
        self.assertIn("**17** jugadores conectados", result.text)
        self.assertIn("Vanderlin", result.text)
        self.assertTrue(result.announce)
        self.assertEqual(result.embed_footer, "Consulta con /estado")


class AnnouncementLogTests(unittest.TestCase):
    def test_remembers_only_the_last_automatic_message(self) -> None:
        folder = Path(__file__).resolve().parent
        path = folder / ".announcements-test.json"
        path.unlink(missing_ok=True)
        try:
            log = AnnouncementLog(path)
            log.load()
            self.assertIsNone(log.get("player_count"))
            log.remember("player_count", 10)
            log.remember("player_count", 20)
            again = AnnouncementLog(path)
            again.load()
            self.assertEqual(again.get("player_count"), 20)
        finally:
            path.unlink(missing_ok=True)

    def test_only_the_bot_message_can_be_removed(self) -> None:
        self.assertTrue(message_belongs_to_bot(7, 7))
        self.assertFalse(message_belongs_to_bot(3, 7))
        self.assertFalse(message_belongs_to_bot(7, None))


class AnnounceTests(unittest.TestCase):
    def test_automatic_notice_only_above_the_minimum(self) -> None:
        config = load_config({})
        feature = PlayerCountFeature(config)
        quiet = feature.run(_PayloadGateway('{"players": 5, "map_name": "Vanderlin"}'), config)
        busy = feature.run(_PayloadGateway('{"players": 6}'), config)
        offline = feature.run(_PayloadGateway('"Commskey disabled"'), config)
        self.assertFalse(quiet.announce)
        self.assertIn("**5** jugadores conectados", quiet.text)
        self.assertTrue(busy.announce)
        self.assertFalse(offline.announce)
        self.assertIn("COMMS_KEY", offline.text)

        lowered = load_config({"MIN_PLAYERS_TO_ANNOUNCE": "0"})
        feature = PlayerCountFeature(lowered)
        self.assertFalse(feature.run(_PayloadGateway('{"players": 0}'), lowered).announce)
        self.assertTrue(feature.run(_PayloadGateway('{"players": 1}'), lowered).announce)

        with self.assertRaises(ConfigError):
            load_config({"MIN_PLAYERS_TO_ANNOUNCE": "-2"})


class ScheduleTests(unittest.TestCase):
    def test_player_count_is_due_every_fifteen_minutes(self) -> None:
        feature = ClockFeature()
        app = App(load_config({}), DemoServerGateway(), features=[feature])
        self.assertEqual(app.due_features(0), [feature])
        self.assertEqual(app.seconds_until_next(0), 0)
        app.mark_ran(feature, 1000)
        self.assertEqual(app.due_features(1000 + 899), [])
        self.assertAlmostEqual(app.seconds_until_next(1000 + 899), 1)
        self.assertEqual(app.due_features(1000 + 900), [feature])
        self.assertEqual(app.seconds_until_next(1000 + 900), 0)

    def test_duplicate_commands_are_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            validate_features([ClockFeature(), ClockFeature()])

    def test_default_feature_list(self) -> None:
        features = build_features(load_config({}))
        self.assertEqual([feature.id for feature in features], ["player_count", "books"])
        self.assertEqual(features[0].interval_seconds, 900)
        self.assertEqual(features[0].command_names, ("estado",))


class ConsoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = App(load_config({}, demo=True), DemoServerGateway())

    def test_commands(self) -> None:
        self.assertIsNone(execute_console_line(self.app, "salir"))
        self.assertIn("estado", execute_console_line(self.app, "ayuda") or "")
        report = execute_console_line(self.app, "estado") or ""
        self.assertIn("**17** jugadores conectados", report)
        self.assertIn("15 minutos", execute_console_line(self.app, "agenda") or "")
        self.assertIn("ejemplo", execute_console_line(self.app, "fuente") or "")
        self.assertIn("BYOND_HOST", execute_console_line(self.app, "demo off") or "")
        self.assertIsInstance(self.app.gateway, DemoServerGateway)
        self.assertIn("desconocido", (self.app.run_command("no-existe").text))


class GatewayTests(unittest.TestCase):
    def test_live_gateway_reads_status_json(self) -> None:
        client = _ScriptedClient(TopicValue(kind="string", text='{"players": 4, "gamestate": 1}'))
        snapshot = LiveServerGateway(client).player_snapshot()
        self.assertEqual(client.queries, [STATUS_QUERY])
        self.assertEqual(snapshot.players, 4)
        self.assertEqual(snapshot.game_state_label, "En lobby")

    def test_live_gateway_reports_connection_errors(self) -> None:
        snapshot = LiveServerGateway(_BrokenClient()).player_snapshot()
        self.assertFalse(snapshot.online)
        self.assertIn("rechazada", snapshot.error or "")

    def test_topic_roundtrip_on_localhost(self) -> None:
        payload = '{"players": 3, "map_name": "Test", "gamestate": 3, "round_duration": 60}'
        with _TopicServer(_response(b"\x06" + payload.encode("ascii") + b"\x00")) as server:
            snapshot = LiveServerGateway(
                ByondTopicClient("127.0.0.1", server.port, timeout=2)
            ).player_snapshot()
        self.assertIn(b"?status&format=json", server.request)
        self.assertEqual(snapshot.players, 3)
        report = format_player_report(snapshot, "Yunque")
        self.assertIn("**3** jugadores conectados", report)
        self.assertIn("**Duración** · 1 min", report)

    def test_connection_refused(self) -> None:
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        client = ByondTopicClient("127.0.0.1", port, timeout=2)
        with self.assertRaises(ByondError) as caught:
            client.query("ping")
        self.assertIn("127.0.0.1", str(caught.exception))


class BookTests(unittest.TestCase):
    def test_html_reads_like_the_in_game_page(self) -> None:
        text = html_fragment_to_text(
            "<p><strong>Title</strong></p><p>A dwarf&apos;s tale.<br>Second line.</p>"
        )
        self.assertEqual(text, "Title\n\nA dwarf's tale.\nSecond line.")
        self.assertNotIn("<", text)

    def test_catalog_matches_a_title_and_builds_a_txt(self) -> None:
        folder = Path(__file__).resolve().parent / "_books"
        folder.mkdir(exist_ok=True)
        definitions = folder / "books.dm"
        library_dir = folder / "strings"
        library_dir.mkdir(exist_ok=True)
        definitions.write_text(
            "\n".join(
                [
                    "/obj/item/book/law",
                    '\tname = "Tome of Justice"',
                    '\tdesc = "The town law."',
                    '\tbookfile = "law.json"',
                    "/obj/item/book/law/small",
                    '\tname = "Pocket Tome of Justice"',
                    '\tdesc = "A smaller copy."',
                ]
            ),
            encoding="utf-8",
        )
        (library_dir / "law.json").write_text(
            json.dumps({"Contents": ["<p>IT IS WRITTEN HERE.</p>"]}),
            encoding="utf-8",
        )
        try:
            library = BookLibrary(definitions, library_dir)
            feature = BooksFeature(library)
            listing = feature.run(None, None, "libros")  # type: ignore[arg-type]
            self.assertIn("Tome of Justice", listing.text)
            self.assertIn("Pocket Tome of Justice", listing.text)
            requested = feature.run(None, None, "libro", "pocket tome")
            self.assertTrue(requested.private)
            self.assertEqual(requested.attachment_name, "Pocket Tome of Justice.txt")
            self.assertIn("IT IS WRITTEN HERE.", requested.attachment_text)
            self.assertIn("A smaller copy.", requested.attachment_text)
            self.assertNotIn("<p>", requested.attachment_text)
        finally:
            for path in library_dir.glob("*"):
                path.unlink()
            library_dir.rmdir()
            definitions.unlink()
            folder.rmdir()

    def test_server_books_include_the_tome_of_justice(self) -> None:
        from books import DEFAULT_BOOKS_DIR, DEFAULT_DEFINITIONS

        library = BookLibrary(DEFAULT_DEFINITIONS, DEFAULT_BOOKS_DIR)
        matches = library.find("Tome of Justice")
        self.assertEqual([book.title for book in matches], ["Tome of Justice"])
        self.assertIn("IT IS WRITTEN", matches[0].body)


class SourceTests(unittest.TestCase):
    def test_discord_adapter_compiles_without_importing_it(self) -> None:
        path = Path(__file__).resolve().parents[1] / "discord_bot.py"
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


class ClockFeature(Feature):
    id = "clock"
    command_names = ("reloj",)
    description = "Prueba de agenda."
    interval_seconds = 900

    def run(self, gateway, config, command: str = "", argument: str = "") -> FeatureResult:
        return FeatureResult(ok=True, text="ok")


class _PayloadGateway:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def player_snapshot(self):
        return snapshot_from_payload(self.payload)


class _ScriptedClient:
    def __init__(self, value: TopicValue) -> None:
        self.value = value
        self.queries: list[str] = []

    def query(self, query: str) -> TopicValue:
        self.queries.append(query)
        return self.value


class _BrokenClient:
    def query(self, query: str) -> TopicValue:
        raise ByondError("Conexion rechazada en 127.0.0.1:1.")


class _TopicServer:
    def __init__(self, response: bytes) -> None:
        self._response = response
        self.request = b""
        self.port = 0
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._thread: threading.Thread | None = None

    def __enter__(self) -> _TopicServer:
        self._socket.bind(("127.0.0.1", 0))
        self.port = self._socket.getsockname()[1]
        self._socket.listen(1)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._socket.close()
        if self._thread:
            self._thread.join(timeout=3)

    def _serve(self) -> None:
        try:
            connection, _ = self._socket.accept()
        except OSError:
            return
        with connection:
            connection.settimeout(2)
            header = _recv_exact(connection, 4)
            if len(header) < 4:
                self.request = header
                return
            length = struct.unpack(">H", header[2:4])[0]
            self.request = header + _recv_exact(connection, length)
            connection.sendall(self._response)


def _response(body: bytes) -> bytes:
    return b"\x00\x83" + struct.pack(">H", len(body)) + body


def _recv_exact(connection: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = connection.recv(size - len(chunks))
        if not piece:
            break
        chunks += piece
    return bytes(chunks)


if __name__ == "__main__":
    unittest.main()
