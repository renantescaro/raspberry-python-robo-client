"""Leitura do joystick via pygame (SDL2)."""

from __future__ import annotations

import os

# Recebe eventos do joystick mesmo sem janela do pygame em foco
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from . import protocol  # noqa: E402
from .bindings import Binding  # noqa: E402

JOYSTICK_EVENTS = (
    pygame.JOYAXISMOTION,
    pygame.JOYBUTTONDOWN,
    pygame.JOYBUTTONUP,
    pygame.JOYHATMOTION,
    pygame.JOYDEVICEADDED,
    pygame.JOYDEVICEREMOVED,
)


KEYBOARD_EVENTS = (
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.WINDOWFOCUSLOST,
    pygame.WINDOWFOCUSGAINED,
    pygame.WINDOWEXPOSED,
)


def init_pygame(keyboard: bool = False) -> None:
    """Inicializa só o necessário (sem áudio) e filtra a fila de eventos."""
    pygame.display.init()
    pygame.joystick.init()
    pygame.event.set_blocked(None)
    allowed = [*JOYSTICK_EVENTS, pygame.QUIT]
    if keyboard:
        allowed += KEYBOARD_EVENTS
    pygame.event.set_allowed(allowed)


class JoystickDevice:
    """Joystick selecionado pelo índice; trata conexão e desconexão a quente."""

    def __init__(self, index: int) -> None:
        self._index = index
        self.joystick: pygame.joystick.JoystickType | None = None
        self.try_open()

    @property
    def connected(self) -> bool:
        return self.joystick is not None

    def try_open(self) -> bool:
        if self.joystick is None and pygame.joystick.get_count() > self._index:
            self.joystick = pygame.joystick.Joystick(self._index)
            self.joystick.init()
            print(f"Joystick conectado: {self.joystick.get_name()}")
        return self.connected

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa conexão/desconexão. Retorna True se o dispositivo mudou."""
        if event.type == pygame.JOYDEVICEADDED and self.joystick is None:
            return self.try_open()
        if (
            event.type == pygame.JOYDEVICEREMOVED
            and self.joystick is not None
            and event.instance_id == self.joystick.get_instance_id()
        ):
            print("Joystick desconectado")
            self.joystick = None
            return True
        return False


class StateReader:
    """Converte o estado atual do joystick em um ControlState do protocolo."""

    def __init__(self, bindings: dict[str, Binding], threshold: float) -> None:
        self._threshold = threshold
        self._digital = (
            (bindings["JOYSTICK_FORWARD"], protocol.FORWARD),
            (bindings["JOYSTICK_BACKWARD"], protocol.BACKWARD),
            (bindings["JOYSTICK_LEFT"], protocol.LEFT),
            (bindings["JOYSTICK_RIGHT"], protocol.RIGHT),
        )
        self._camera_v = bindings["JOYSTICK_CAMERA_V"]
        self._camera_h = bindings["JOYSTICK_CAMERA_H"]

    def read(self, joystick: pygame.joystick.JoystickType | None) -> protocol.ControlState:
        if joystick is None:
            return protocol.ControlState()
        flags = 0
        for binding, flag in self._digital:
            if self._pressed(joystick, binding):
                flags |= flag
        return protocol.ControlState(
            flags,
            self._axis_direction(joystick, self._camera_v),
            self._axis_direction(joystick, self._camera_h),
        )

    def _pressed(self, joystick: pygame.joystick.JoystickType, binding: Binding) -> bool:
        if binding.kind == "button":
            return binding.index < joystick.get_numbuttons() and bool(
                joystick.get_button(binding.index)
            )
        if binding.index >= joystick.get_numaxes():
            return False
        value = joystick.get_axis(binding.index)
        if binding.direction:
            return value * binding.direction > self._threshold
        return abs(value) > self._threshold

    def _axis_direction(self, joystick: pygame.joystick.JoystickType, binding: Binding) -> int:
        if binding.kind != "axis" or binding.index >= joystick.get_numaxes():
            return 0
        value = joystick.get_axis(binding.index)
        if value > self._threshold:
            return 1
        if value < -self._threshold:
            return -1
        return 0
