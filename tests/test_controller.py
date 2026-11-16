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

    def packets(self) -> list[protocol.ControlState | protocol.Command]:
        size = protocol.PACKET_SIZE
        return [protocol.decode_packet(self.data, i) for i in range(0, len(self.data) - size + 1, size)]

    def commands(self) -> list[protocol.Command]:
        return [p for p in self.packets() if isinstance(p, protocol.Command)]


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


def click(pos) -> None:
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


@pytest.fixture
def keyboard_client(wait, monkeypatch):
    """Cliente só com teclado (com janela) conectado a um Receiver."""
    # Nada pressionado
    monkeypatch.setattr(
        pygame.key, "get_pressed", lambda: type("P", (), {"__getitem__": lambda s, k: False})()
    )
    receiver = Receiver()
    settings = replace(BASE_SETTINGS, server_port=receiver.port, bindings={}, keyboard_enabled=True)
    thread, errors = start_controller(settings)
    assert wait(lambda: len(receiver.packets()) >= 1, timeout=3)
    yield receiver
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    thread.join(timeout=5)
    assert not errors, errors
    assert not thread.is_alive()


def button_center() -> tuple[int, int]:
    from robot_client.control_window import BUTTON_SIZE, PADDING, STATUS_ONLY_SIZE

    return STATUS_ONLY_SIZE[0] - PADDING - BUTTON_SIZE[0] // 2, PADDING + BUTTON_SIZE[1] // 2


def test_shutdown_needs_confirmation_click(keyboard_client, wait):
    receiver = keyboard_client
    click(button_center())
    time.sleep(0.3)
    assert receiver.commands() == []  # um clique só pede confirmação
    click(button_center())
    assert wait(lambda: receiver.commands() == [protocol.Command(protocol.SHUTDOWN)], timeout=3)


def test_shutdown_confirmation_expires(keyboard_client, wait, monkeypatch):
    from robot_client import controller

    monkeypatch.setattr(controller, "SHUTDOWN_CONFIRM_S", 0.2)
    receiver = keyboard_client
    click(button_center())
    time.sleep(0.6)  # passa do prazo (o loop acorda a cada heartbeat de 0.1 s)
    click(button_center())  # vira um novo pedido de confirmação, não um envio
    time.sleep(0.3)
    assert receiver.commands() == []


def test_click_outside_button_does_nothing(keyboard_client):
    receiver = keyboard_client
    click((10, 140))
    click((10, 140))
    time.sleep(0.3)
    assert receiver.commands() == []
