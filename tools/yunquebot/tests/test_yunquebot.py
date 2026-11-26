"""Comprueba el bot sin Discord y, salvo un socket local, sin red."""

from __future__ import annotations

import json
import socket
import struct
import tempfile
import threading
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from bot.interfaces.announcements import AnnouncementLog, message_belongs_to_bot
from bot.game.books import DEFAULT_BOOKS_DIR, DEFAULT_DEFINITIONS, BookLibrary, html_fragment_to_text
from bot.game.player_books import MAX_TEXT_LEN, PlayerBookLibrary, encode_title
from bot.features.book_writing import BookWritingFeature
from bot.features.writer_bans import WriterBans
from bot.features.books import PLAYER_BOOK_MESSAGE_LIMIT, BooksFeature
from bot.app import App
from bot.server.byond import (
    ByondError,
    ByondTopicClient,
    TopicValue,
    decode_topic_response,
    encode_topic_query,
)
from bot.config import (
    CONFIG_DIR,
    DEFAULT_PLAYER_BOOKS_DIR,
    REPO_ROOT,
    TOOL_ROOT,
    ConfigError,
    Permissions,
    load_config,
    load_permissions,
    parse_dotenv,
    parse_permissions,
)
from bot.interfaces.console import execute_console_line
from bot.interfaces.request_log import Request, RequestLog
from bot.features import build_features
from bot.features.player_count import PlayerCountFeature
from bot.features.base import CONSOLE_REQUESTER, Feature, FeatureResult, Requester, validate_features
from bot.formatting import format_player_report, split_text
from bot.server.gateway import STATUS_QUERY, DemoServerGateway, LiveServerGateway, build_gateway
from bot.server.snapshot import snapshot_from_payload


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

    def test_permissions_file(self) -> None:
        permissions = parse_permissions(
            "# comentario\n\n[canales]\n111  # general\n222\n111\n"
            "[administradores]\n333\n[comandos_admin]\n/Libro\n"
        )
        self.assertEqual(permissions.channel_ids, frozenset({111, 222}))
        self.assertEqual(permissions.admin_ids, frozenset({333}))
        self.assertEqual(permissions.admin_commands, frozenset({"libro"}))
        for bad in ("111\n", "[otra]\n", "[canales]\nabc\n", "[administradores]\n-5\n"):
            with self.assertRaises(ConfigError):
                parse_permissions(bad)
        self.assertEqual(load_permissions(Path(__file__).resolve().parent / "no-existe.txt"), Permissions())
        template = CONFIG_DIR / "permisos.example.txt"
        self.assertEqual(load_permissions(template), Permissions())

    def test_empty_permissions_allow_everything(self) -> None:
        anywhere = load_config({}).permissions
        self.assertTrue(anywhere.accepts_channel(999))
        self.assertTrue(anywhere.accepts_channel(None))
        self.assertTrue(anywhere.allows_command("libro", 999))

        limited = Permissions(
            channel_ids=frozenset({111}),
            admin_ids=frozenset({333}),
            admin_commands=frozenset({"libro"}),
        )
        self.assertTrue(limited.accepts_channel(111))
        self.assertTrue(limited.accepts_channel(555, parent_id=111))
        self.assertFalse(limited.accepts_channel(999))
        self.assertFalse(limited.accepts_channel(None))
        self.assertTrue(limited.accepts_channel(999, private=True))
        self.assertTrue(limited.allows_command("libro", 333))
        self.assertFalse(limited.allows_command("libro", 999))
        self.assertTrue(limited.allows_command("estado", 999))

    def test_unknown_admin_command_is_rejected(self) -> None:
        permissions = Permissions(admin_commands=frozenset({"reiniciar"}))
        with self.assertRaises(ConfigError):
            App(load_config({}, demo=True, permissions=permissions), DemoServerGateway())

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


class RequestLogTests(unittest.TestCase):
    def test_one_file_per_command_and_entries_are_appended(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            logs = RequestLog(Path(folder) / "logs")
            when = datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)
            book = Request("libro", "Pepe (@pepe, id 7)", "Mensaje privado", {"titulo": "Tome"})
            logs.record(book, "respondido", "Te lo envié.\nAdjunto por privado: Tome.txt", when)
            logs.record(book, "respondido sin éxito", "No encontré nada.", when)
            logs.record(Request("biblioteca", "Ana (@ana, id 8)", "Yunque / #general"), "respondido", "1. Tome")

            text = logs.path_for("libro").read_text(encoding="utf-8")
            self.assertEqual(text.count("Usuario: Pepe (@pepe, id 7)"), 2)
            self.assertIn("[2026-11-18 12:00:00 +0000] respondido\n", text)
            self.assertIn("Parámetros: titulo = Tome", text)
            self.assertIn("    Adjunto por privado: Tome.txt", text)
            self.assertIn("No encontré nada.", text)

            listing = (Path(folder) / "logs" / "biblioteca.txt").read_text(encoding="utf-8")
            self.assertIn("Parámetros: (ninguno)", listing)
            self.assertNotIn("Pepe", listing)


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
        self.assertEqual([feature.id for feature in features], ["player_count", "books", "book_writing"])
        self.assertEqual(features[0].interval_seconds, 900)
        self.assertEqual(features[0].command_names, ("estado",))
        self.assertEqual(features[1].command_names, ("biblioteca", "libro"))


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
            feature = BooksFeature({"codigo": library})
            listing = feature.run(None, None, "biblioteca", "codigo")  # type: ignore[arg-type]
            self.assertTrue(listing.ok)
            self.assertEqual(listing.embed_title, "Libros del código")
            self.assertIn("Tome of Justice", listing.text)
            self.assertIn("Pocket Tome of Justice", listing.text)
            self.assertIn("/libro", listing.text)
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

    def test_library_has_three_listings(self) -> None:
        feature = BooksFeature({})
        self.assertEqual(
            [label for _, label in feature.command_choices("biblioteca")],
            ["Libros del código", "Libros de trabajos", "Libros de jugadores"],
        )
        self.assertEqual(feature.command_argument("biblioteca"), "listado")
        self.assertEqual(feature.command_choices("libro"), ())

        pending = feature.run(None, None, "biblioteca", "trabajos")  # type: ignore[arg-type]
        self.assertFalse(pending.ok)
        self.assertIn("Libros de trabajos", pending.text)
        self.assertIn("todavía no está disponible", pending.text)
        by_label = feature.run(None, None, "biblioteca", "libros de jugadores")  # type: ignore[arg-type]
        self.assertIn("Libros de jugadores", by_label.text)

        unknown = feature.run(None, None, "biblioteca", "")  # type: ignore[arg-type]
        self.assertFalse(unknown.ok)
        for key in ("codigo", "trabajos", "jugadores"):
            self.assertIn(key, unknown.text)

    def test_server_books_include_the_tome_of_justice(self) -> None:
        from bot.game.books import DEFAULT_BOOKS_DIR, DEFAULT_DEFINITIONS

        library = BookLibrary(DEFAULT_DEFINITIONS, DEFAULT_BOOKS_DIR)
        matches = library.find("Tome of Justice")
        self.assertEqual([book.title for book in matches], ["Tome of Justice"])
        self.assertIn("IT IS WRITTEN", matches[0].body)


class PlayerBookTests(unittest.TestCase):
    PARAGRAPH = "Dicen que los Aasimar son creados por y para los Diez. " * 6

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.folder = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _write(self, name: str, payload: object) -> None:
        (self.folder / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    def _aasimar(self) -> None:
        body = "<br><br>".join([self.PARAGRAPH] * 5)
        self._write(
            "El+Misterio+de+los+Aasimar",
            {
                "book_title": "El Misterio de los Aasimar",
                "author": "Nimrod",
                "author_ckey": "elcuradetuiglesia",
                "icon": "book6",
                "text": f'<p></p>\n<p><font face="Segoe Script" color=#14103f>{body}</font></p>\n',
                "category": "Thesis",
            },
        )

    def test_catalog_follows_the_game_index(self) -> None:
        self._aasimar()
        self._write("Unknown", {"book_title": "Unknown Title", "author": "Unknown Author", "text": "Ilegible"})
        self._write("Borrado", {"book_title": "Borrado", "author": "X", "text": "Ya no está en el índice"})
        self._write("_book_titles", ["El+Misterio+de+los+Aasimar", "Unknown", "Falta", "_book_titles"])

        books = PlayerBookLibrary(self.folder).catalog()
        self.assertEqual([book.title for book in books], ["El Misterio de los Aasimar", "Unknown Title"])
        self.assertEqual(books[0].label(), "El Misterio de los Aasimar — Nimrod")
        self.assertEqual(books[1].category, "Thesis")
        self.assertNotIn("<", books[0].body)

    def test_without_index_every_json_is_a_book(self) -> None:
        self._aasimar()
        (self.folder / "roto.json").write_text("{no es json", encoding="utf-8")
        books = PlayerBookLibrary(self.folder).catalog()
        self.assertEqual([book.title for book in books], ["El Misterio de los Aasimar"])
        self.assertTrue(PlayerBookLibrary(self.folder / "no-existe").problem())

    def test_player_book_arrives_in_short_messages(self) -> None:
        self._aasimar()
        feature = BooksFeature({"jugadores": PlayerBookLibrary(self.folder)})
        listing = feature.run(None, None, "biblioteca", "jugadores")  # type: ignore[arg-type]
        self.assertTrue(listing.ok)
        self.assertIn("1. El Misterio de los Aasimar — Nimrod", listing.text)

        result = feature.run(None, None, "libro", "misterio aasimar")  # type: ignore[arg-type]
        self.assertTrue(result.private)
        self.assertFalse(result.attachment_text)
        self.assertGreater(len(result.private_messages), 2)
        self.assertTrue(all(len(message) <= PLAYER_BOOK_MESSAGE_LIMIT for message in result.private_messages))
        self.assertIn("El Misterio de los Aasimar", result.private_messages[0])
        self.assertIn("Nimrod", result.private_messages[0])
        self.assertEqual(" ".join(" ".join(result.private_messages[1:]).split()).count("Aasimar"), 30)

    def test_libro_searches_code_and_player_books(self) -> None:
        self._write("Tome+of+Justice", {"book_title": "Tome of Justice", "author": "Ana", "text": "Copia"})
        feature = BooksFeature(
            {
                "codigo": BookLibrary(DEFAULT_DEFINITIONS, DEFAULT_BOOKS_DIR),
                "jugadores": PlayerBookLibrary(self.folder),
            }
        )
        both = feature.run(None, None, "libro", "tome of")  # type: ignore[arg-type]
        self.assertFalse(both.ok)
        self.assertIn("(Libros del código)", both.text)
        self.assertIn("(Libros de jugadores)", both.text)

    def test_folder_comes_from_the_configuration(self) -> None:
        self.assertEqual(load_config({}).player_books_dir, DEFAULT_PLAYER_BOOKS_DIR)
        self.assertEqual(load_config({"PLAYER_BOOKS_DIR": "otra/carpeta"}).player_books_dir, REPO_ROOT / "otra" / "carpeta")
        absolute = self.folder.resolve()
        self.assertEqual(load_config({"PLAYER_BOOKS_DIR": str(absolute)}).player_books_dir, absolute)
        features = build_features(load_config({"PLAYER_BOOKS_DIR": str(absolute)}))
        self.assertEqual(features[1].libraries["jugadores"].folder, absolute)

    def test_split_text_respects_the_limit(self) -> None:
        text = "Primera frase. " * 80 + "\n\n" + "x" * 1200
        chunks = split_text(text, 500)
        self.assertTrue(all(0 < len(chunk) <= 500 for chunk in chunks))
        self.assertEqual("".join(chunks).replace(" ", "").replace("\n", ""), text.replace(" ", "").replace("\n", ""))
        self.assertTrue(chunks[0].endswith("."))
        self.assertEqual(split_text("corto", 500), ["corto"])


class BookWritingTests(unittest.TestCase):
    ANA = Requester(key="discord:1", name="Ana", account="ana_01")
    LUIS = Requester(key="discord:2", name="Luis", account="luis")

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.folder = Path(self._temp.name)
        self.library = PlayerBookLibrary(self.folder)
        self.feature = BookWritingFeature(self.library)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _run(self, command: str, argument: str = "", requester: Requester | None = None) -> FeatureResult:
        return self.feature.run(None, None, command, argument, requester or self.ANA)  # type: ignore[arg-type]

    def test_titles_are_encoded_like_byond(self) -> None:
        self.assertEqual(encode_title("El Misterio de los Aasimar"), "El+Misterio+de+los+Aasimar")
        self.assertEqual(encode_title("Año & día"), "A%C3%B1o+%26+d%C3%ADa")

    def test_a_book_is_written_and_saved_like_the_game(self) -> None:
        (self.folder / "_book_titles.json").write_text('["Viejo"]', encoding="utf-8")
        start = self._run("escribir_libro", "  El   Libro de Ana ")
        self.assertTrue(start.ok)
        self.assertTrue(start.private)
        self.assertIn("El Libro de Ana", start.private_messages[0])

        self.assertIsNone(self.feature.capture_text(self.LUIS, "Esto no es de Ana"))
        self.assertTrue(self.feature.capture_text(self.ANA, "Primer párrafo <b>sin HTML</b>.").accepted)
        self.assertTrue(self.feature.capture_text(self.ANA, "Segunda línea\ny tercera.").accepted)
        self.assertFalse(self.feature.capture_text(self.ANA, "   ").accepted)

        self.assertFalse(self._run("terminar_libro", "Poesía").ok)
        done = self._run("terminar_libro", "myths & tales")
        self.assertTrue(done.ok, done.text)
        self.assertIsNone(self.feature.draft_for(self.ANA))

        saved = json.loads((self.folder / "El+Libro+de+Ana.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["book_title"], "El Libro de Ana")
        self.assertEqual(saved["author"], "Ana")
        self.assertEqual(saved["author_ckey"], "ana_01")
        self.assertEqual(saved["icon"], "basic_book")
        self.assertEqual(saved["category"], "Myths & Tales")
        self.assertEqual(
            saved["text"],
            "<p>Primer párrafo &lt;b&gt;sin HTML&lt;/b&gt;.</p>\n<p>Segunda línea<br>y tercera.</p>\n",
        )
        index = json.loads((self.folder / "_book_titles.json").read_text(encoding="utf-8"))
        self.assertEqual(index, ["Viejo", "El+Libro+de+Ana"])

        book = self.library.find("libro ana")[0]
        self.assertEqual(book.body, "Primer párrafo <b>sin HTML</b>.\n\nSegunda línea\ny tercera.")

    def test_the_writer_chooses_the_author(self) -> None:
        start = self.feature.run(None, None, "escribir_libro", "Crónica <i>", self.ANA, "  Fray   <b>Anselmo</b> ")  # type: ignore[arg-type]
        self.assertTrue(start.ok, start.text)
        self.assertIn("de Fray b Anselmo /b", start.private_messages[0])
        self.feature.capture_text(self.ANA, "Texto")
        done = self._run("terminar_libro", "Thesis")
        self.assertIn("de Fray b Anselmo /b", done.text)
        saved = json.loads((self.folder / "Cr%C3%B3nica+i.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["book_title"], "Crónica i")
        self.assertEqual(saved["author"], "Fray b Anselmo /b")
        self.assertEqual(saved["author_ckey"], "ana_01")

        too_long = self.feature.run(None, None, "escribir_libro", "Otro", self.LUIS, "x" * 81)  # type: ignore[arg-type]
        self.assertIn("80", too_long.text)
        self.assertIsNone(self.feature.draft_for(self.LUIS))

    def test_without_index_the_existing_books_are_kept(self) -> None:
        self._write_book("Antiguo", "Antiguo")
        self._run("escribir_libro", "Nuevo")
        self.feature.capture_text(self.ANA, "Texto")
        self.assertTrue(self._run("terminar_libro", "Thesis").ok)
        titles = [book.title for book in self.library.catalog()]
        self.assertEqual(titles, ["Antiguo", "Nuevo"])

    def test_rules_of_a_draft(self) -> None:
        self._write_book("Repetido", "Repetido")
        self.assertIn("Ya hay un libro", self._run("escribir_libro", "repetido").text)
        self.assertIn("80", self._run("escribir_libro", "x" * 81).text)
        self.assertFalse(self._run("escribir_libro", "_book_titles").ok)
        self.assertIn("No estás escribiendo", self._run("terminar_libro", "Thesis").text)

        self.assertTrue(self._run("escribir_libro", "Uno").ok)
        self.assertIn("Ya estás escribiendo «Uno»", self._run("escribir_libro", "Dos").text)
        self.assertIn("Todavía no me has enviado texto", self._run("terminar_libro", "Thesis").text)
        too_long = self.feature.capture_text(self.ANA, "x" * (MAX_TEXT_LEN + 1))
        self.assertFalse(too_long.accepted)
        self.assertIn(str(MAX_TEXT_LEN), too_long.reply)
        self.assertTrue(self.feature.capture_text(self.ANA, "x" * MAX_TEXT_LEN).accepted)
        self.assertFalse(self.feature.capture_text(self.ANA, "y").accepted)

        self.assertIn("Descartado «Uno»", self._run("cancelar_libro").text)
        self.assertIsNone(self.feature.capture_text(self.ANA, "ya no hay borrador"))
        self.assertFalse((self.folder / "Uno.json").exists())

    def test_console_writes_a_book_line_by_line(self) -> None:
        app = App(
            load_config({"PLAYER_BOOKS_DIR": str(self.folder.resolve())}, demo=True),
            DemoServerGateway(),
        )
        self.assertIn(
            "Escribiendo «Diario», de Maese Pere.",
            execute_console_line(app, "escribir_libro Diario | Maese Pere") or "",
        )
        self.assertIn("Llevas", execute_console_line(app, "Hoy llovió en Kingsfield.") or "")
        self.assertIn("Guardado «Diario»", execute_console_line(app, "terminar_libro Thesis") or "")
        self.assertIn("desconocido", execute_console_line(app, "esto ya no se guarda") or "")
        saved = json.loads((self.folder / "Diario.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["author"], "Maese Pere")
        self.assertEqual(saved["author_ckey"], CONSOLE_REQUESTER.account)

    def test_admins_ban_and_unban_writers(self) -> None:
        bans_path = self.folder / "datos" / "baneados_libros.json"
        feature = BookWritingFeature(self.library, WriterBans(bans_path))
        config = load_config({}, permissions=Permissions(admin_ids=frozenset({9})))
        admin = Requester(key="discord:9", name="Admin")

        def run(command: str, argument: str = "", requester: Requester = self.ANA) -> FeatureResult:
            return feature.run(None, config, command, argument, requester)  # type: ignore[arg-type]

        self.assertTrue(run("escribir_libro", "A medias").ok)
        self.assertTrue(feature.capture_text(self.ANA, "Texto").accepted)
        banned = run("banear_escritor", "<@1>", admin)
        self.assertTrue(banned.ok, banned.text)
        self.assertIn("«A medias»", banned.text)
        self.assertIsNone(feature.draft_for(self.ANA))
        self.assertIsNone(feature.capture_text(self.ANA, "Más texto"))
        self.assertIn("prohibido", run("escribir_libro", "Otro").text)
        self.assertIn("ya tenía", run("banear_escritor", "1", admin).text)
        self.assertIn("administrador", run("banear_escritor", "9", admin).text)
        self.assertFalse(run("banear_escritor", "Ana", admin).ok)
        self.assertTrue(run("escribir_libro", "De Luis", self.LUIS).ok)

        saved = json.loads(bans_path.read_text(encoding="utf-8"))
        self.assertEqual(list(saved), ["discord:1"])
        self.assertEqual(saved["discord:1"]["por"], "Admin (discord:9)")
        reloaded = BookWritingFeature(self.library, WriterBans(bans_path))
        listing = reloaded.run(None, config, "escritores_baneados", "", admin)  # type: ignore[arg-type]
        self.assertIn("<@1> (id 1), por Admin (discord:9)", listing.text)

        self.assertTrue(run("desbanear_escritor", "discord:1", admin).ok)
        self.assertIn("no estaba", run("desbanear_escritor", "1", admin).text)
        self.assertTrue(run("escribir_libro", "Otro").ok)
        self.assertEqual(json.loads(bans_path.read_text(encoding="utf-8")), {})
        self.assertIn("Nadie", run("escritores_baneados", "", admin).text)

    def test_a_broken_ban_list_stops_the_bot(self) -> None:
        path = self.folder / "baneados_libros.json"
        path.write_text("{roto", encoding="utf-8")
        with self.assertRaises(ConfigError):
            WriterBans(path)

    def test_ban_commands_are_always_for_admins(self) -> None:
        config = replace(
            load_config({"PLAYER_BOOKS_DIR": str(self.folder.resolve())}, demo=True),
            permissions=Permissions(admin_ids=frozenset({9})),
            writer_bans_path=None,
        )
        app = App(config, DemoServerGateway())
        self.assertEqual(
            app.admin_command_names(), ["banear_escritor", "desbanear_escritor", "escritores_baneados"]
        )
        self.assertFalse(app.allows_command("banear_escritor", 1))
        self.assertTrue(app.allows_command("banear_escritor", 9))
        self.assertTrue(app.allows_command("escribir_libro", 1))
        self.assertIn("ya no puede", execute_console_line(app, "banear_escritor 1") or "")

    def _write_book(self, name: str, title: str) -> None:
        (self.folder / f"{name}.json").write_text(
            json.dumps({"book_title": title, "author": "X", "text": "Algo"}), encoding="utf-8"
        )


class SourceTests(unittest.TestCase):
    def test_discord_adapter_compiles_without_importing_it(self) -> None:
        path = TOOL_ROOT / "bot" / "interfaces" / "discord_bot.py"
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


class ClockFeature(Feature):
    id = "clock"
    command_names = ("reloj",)
    description = "Prueba de agenda."
    interval_seconds = 900

    def run(self, gateway, config, command: str = "", argument: str = "", requester=None, extra: str = "") -> FeatureResult:
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
