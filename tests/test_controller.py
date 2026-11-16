"""Testes de integração do loop principal (pygame real, sem joystick)."""

from __future__ import annotations

import socket
import threading
import time
from dataclasses import replace

import pygame
import pytest

from robot_client import protocol
from robot_client.bindings import Binding
from robot_client.controller import run_controller
from robot_client.settings import DEFAULT_KEYS, Settings

BINDINGS = {
    "JOYSTICK_FORWARD": Binding("button", 0),
    "JOYSTICK_BACKWARD": Binding("button", 1),
    "JOYSTICK_LEFT": Binding("axis", 0, -1),
    "JOYSTICK_RIGHT": Binding("axis", 0, 1),
    "JOYSTICK_CAMERA_V": Binding("axis", 3),
    "JOYSTICK_CAMERA_H": Binding("axis", 2),
}

BASE_SETTINGS = Settings(
    server_host="127.0.0.1",
    server_port=0,
    axis_threshold=0.4,
    heartbeat_s=0.1,
    joystick_index=0,
    bindings=BINDINGS,
    keyboard_enabled=False,
    key_bindings=DEFAULT_KEYS,
    video_enabled=False,
    streaming_url=None,
    video_size=(800, 600),
    video_rotate_180=True,
    face_detection=False,
)


class Receiver:
    """Servidor TCP mínimo que acumula os bytes recebidos."""

    def __init__(self) -> None:
        self.server = socket.create_server(("127.0.0.1", 0))
        self.server.settimeout(5)
        self.data = bytearray()
        self.closed = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    @property
    def port(self) -> int:
        return self.server.getsockname()[1]

    def _run(self) -> None:
        connection, _ = self.server.accept()
        with connection:
            while chunk := connection.recv(64):
                self.data += chunk
        self.closed.set()

    def packets(self) -> list[protocol.ControlState]:
        size = protocol.PACKET_SIZE
        return [protocol.decode(self.data, i) for i in range(0, len(self.data) - size + 1, size)]


def test_requires_server_host():
    with pytest.raises(SystemExit):
        run_controller(replace(BASE_SETTINGS, server_host=None))


def test_requires_joystick_or_keyboard():
    with pytest.raises(SystemExit, match="KEYBOARD_ENABLED"):
        run_controller(replace(BASE_SETTINGS, bindings={}, keyboard_enabled=False))


def start_controller(settings: Settings) -> tuple[threading.Thread, list[BaseException]]:
    errors: list[BaseException] = []

    def target() -> None:
        try:
            run_controller(settings)
        except BaseException as exc:  # noqa: BLE001 - repassa para a thread do teste
            errors.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, errors


def test_keyboard_only_drives_robot_and_esc_quits(wait, monkeypatch):
    """Sem joystick mapeado: teclado controla, Esc encerra enviando parada."""
    held: set[int] = set()

    class Pressed:
        def __getitem__(self, code: int) -> bool:
            return code in held

    # Eventos postados não alteram o estado real do teclado no SDL; simulamos o get_pressed
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: Pressed())

    receiver = Receiver()
    settings = replace(BASE_SETTINGS, server_port=receiver.port, bindings={}, keyboard_enabled=True)
    thread, errors = start_controller(settings)
    try:
        assert wait(lambda: len(receiver.packets()) >= 1, timeout=3)

        held.update({pygame.K_w, pygame.K_l})
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
        expected = protocol.ControlState(protocol.FORWARD, 0, 1)
        assert wait(lambda: expected in receiver.packets(), timeout=3)

        held.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_w))
        assert wait(lambda: receiver.packets()[-1] == protocol.ControlState(), timeout=3)
    finally:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        thread.join(timeout=5)

    assert not errors, errors
    assert not thread.is_alive()
    assert receiver.closed.wait(2)
    assert receiver.packets()[-1] == protocol.ControlState()


def test_sends_heartbeats_and_stops_on_quit(wait):
    receiver = Receiver()
    settings = replace(BASE_SETTINGS, server_port=receiver.port)
    errors: list[BaseException] = []

    def target() -> None:
        try:
            run_controller(settings)
        except BaseException as exc:  # noqa: BLE001 - repassa para a thread do teste
            errors.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    try:
        # heartbeat de 0.1 s: em ~0.6 s espera vários pacotes, todos "parado"
        assert wait(lambda: len(receiver.packets()) >= 4, timeout=3)
    finally:
        time.sleep(0.05)
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        thread.join(timeout=5)

    assert not errors, errors
    assert not thread.is_alive()
    assert receiver.closed.wait(2)
    packets = receiver.packets()
    assert all(state == protocol.ControlState() for state in packets)
    # Ao sair, o último pacote enviado é o de parada
    assert packets[-1] == protocol.ControlState()
