"""Cliente del protocolo world.Topic de BYOND.

El paquete esta documentado por el formato clasico de DreamDaemon:
2 bytes 0x00 0x83, longitud big-endian de lo que sigue, 5 bytes nulos,
la consulta que empieza por '?' y un nulo final.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass

TOPIC_SIGNATURE = b"\x00\x83"
RESPONSE_NULL = 0x00
RESPONSE_STRING = 0x06
RESPONSE_FLOAT = 0x2A
MAX_RESPONSE_BYTES = 1024 * 1024


class ByondError(Exception):
    """No se pudo completar una consulta al servidor."""


@dataclass(frozen=True)
class TopicValue:
    kind: str
    text: str | None = None
    number: float | None = None


def encode_topic_query(query: str) -> bytes:
    if not query.startswith("?"):
        query = "?" + query
    try:
        message = query.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ByondError("La consulta topic solo puede contener ASCII.") from exc
    body = (b"\x00" * 5) + message + b"\x00"
    return TOPIC_SIGNATURE + struct.pack(">H", len(body)) + body


def decode_topic_response(packet: bytes) -> TopicValue:
    if len(packet) < 4 or packet[:2] != TOPIC_SIGNATURE:
        raise ByondError("El servidor no respondió con un paquete topic.")
    length = struct.unpack(">H", packet[2:4])[0]
    body = packet[4 : 4 + length]
    if len(body) < length:
        raise ByondError("La respuesta del servidor llegó incompleta.")
    if not body:
        return TopicValue(kind="null")

    type_code = body[0]
    payload = body[1:]
    if type_code == RESPONSE_NULL:
        return TopicValue(kind="null")
    if type_code == RESPONSE_STRING:
        text = payload.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        return TopicValue(kind="string", text=text)
    if type_code == RESPONSE_FLOAT:
        if len(payload) < 4:
            raise ByondError("El servidor envió un número incompleto.")
        number = struct.unpack(">f", payload[:4])[0]
        if number != number:  # NaN
            raise ByondError("El servidor envió un número inválido.")
        return TopicValue(kind="number", number=number)
    raise ByondError(f"Tipo de respuesta topic no soportado: {type_code:#x}.")


class ByondTopicClient:
    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def query(self, query: str) -> TopicValue:
        packet = encode_topic_query(query)
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(packet)
                header = _recvall(sock, 4)
                if header[:2] != TOPIC_SIGNATURE:
                    raise ByondError("El servidor no respondió con un paquete topic.")
                length = struct.unpack(">H", header[2:4])[0]
                if length > MAX_RESPONSE_BYTES:
                    raise ByondError("La respuesta del servidor es demasiado grande.")
                body = _recvall(sock, length) if length else b""
        except ByondError:
            raise
        except TimeoutError as exc:
            raise ByondError(f"Tiempo de espera agotado al consultar {self.host}:{self.port}.") from exc
        except ConnectionRefusedError as exc:
            raise ByondError(f"Conexión rechazada en {self.host}:{self.port}.") from exc
        except OSError as exc:
            raise ByondError(f"No se pudo consultar {self.host}:{self.port}: {exc}") from exc
        return decode_topic_response(header + body)


def _recvall(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ByondError("El servidor cerró la conexión antes de completar la respuesta.")
        chunks += chunk
    return bytes(chunks)
