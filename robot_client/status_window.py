"""Janela de status do cliente; também é ela que recebe o teclado."""

from __future__ import annotations

import pygame

from . import protocol

WINDOW_SIZE = (520, 150)
BACKGROUND = (24, 26, 31)
TEXT = (230, 232, 236)
MUTED = (140, 146, 158)
OK = (110, 200, 120)
WARN = (235, 170, 80)

_MOVES = (
    (protocol.FORWARD, "frente"),
    (protocol.BACKWARD, "ré"),
    (protocol.LEFT, "esquerda"),
    (protocol.RIGHT, "direita"),
)


def describe_state(state: protocol.ControlState) -> str:
    parts = [name for flag, name in _MOVES if state.flags & flag]
    camera = []
    # Palavras em vez de setas: a fonte padrão do pygame não tem esses glifos
    if state.camera_v:
        camera.append("cima" if state.camera_v < 0 else "baixo")
    if state.camera_h:
        camera.append("esquerda" if state.camera_h < 0 else "direita")
    if camera:
        parts.append("câmera " + "/".join(camera))
    return " + ".join(parts) if parts else "parado"


class StatusWindow:
    def __init__(self, help_lines: list[str]) -> None:
        self._screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Controle do robô")
        pygame.font.init()
        self._font = pygame.font.Font(None, 22)
        self._help = help_lines
        self._last: tuple | None = None

    def update(
        self,
        connected: bool,
        server: str,
        joystick_name: str | None,
        state: protocol.ControlState,
        force: bool = False,
    ) -> None:
        # Só redesenha quando algo muda
        key = (connected, joystick_name, state)
        if key == self._last and not force:
            return
        self._last = key

        lines = [
            (f"Robô: conectado a {server}" if connected else f"Robô: sem conexão ({server})",
             OK if connected else WARN),
            (f"Joystick: {joystick_name}" if joystick_name else "Joystick: nenhum", TEXT),
            (f"Comando: {describe_state(state)}", TEXT),
            *((line, MUTED) for line in self._help),
        ]
        self._screen.fill(BACKGROUND)
        y = 14
        for text, color in lines:
            self._screen.blit(self._font.render(text, True, color), (14, y))
            y += 24
        pygame.display.flip()
