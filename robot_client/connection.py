"""Conexão TCP com o robô, com reconexão automática."""

from __future__ import annotations

import socket
import time

CONNECT_TIMEOUT_S = 2.0
SEND_TIMEOUT_S = 1.0


class RobotConnection:
    def __init__(self, host: str, port: int, retry_interval_s: float = 1.0) -> None:
        self._address = (host, port)
        self._retry_interval = retry_interval_s
        self._sock: socket.socket | None = None
        self._next_attempt = 0.0

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def send(self, data: bytes) -> bool:
        """Envia os dados; conecta/reconecta se necessário. Retorna True se enviou."""
        if self._sock is None and not self._connect():
            return False
        try:
            self._sock.sendall(data)
            return True
        except OSError as exc:
            print(f"Conexão perdida: {exc}")
            self.close()
            return False

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def _connect(self) -> bool:
        now = time.monotonic()
        if now < self._next_attempt:
            return False
        self._next_attempt = now + self._retry_interval
        try:
            sock = socket.create_connection(self._address, timeout=CONNECT_TIMEOUT_S)
        except OSError as exc:
            print(f"Sem conexão com {self._address[0]}:{self._address[1]} ({exc})")
            return False
        # Desliga o algoritmo de Nagle: pacotes pequenos saem imediatamente
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(SEND_TIMEOUT_S)
        self._sock = sock
        print(f"Conectado ao robô em {self._address[0]}:{self._address[1]}")
        return True
