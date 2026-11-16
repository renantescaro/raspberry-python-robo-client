"""Janela "Controle do robô": vídeo da câmera com o status sobreposto.

É também a janela que recebe o teclado (o pygame só lê teclas com janela
própria em foco). Desenho barato: o painel de status é renderizado só quando
muda e o quadro do vídeo vem pronto da thread (já girado e redimensionado),
usado sem cópia via `pygame.image.frombuffer`.
"""

from __future__ import annotations

import pygame

from . import protocol

STATUS_ONLY_SIZE = (520, 150)
BACKGROUND = (12, 13, 16)
PANEL = (0, 0, 0, 150)
TEXT = (230, 232, 236)
MUTED = (170, 176, 188)
OK = (110, 200, 120)
WARN = (235, 170, 80)
LINE_HEIGHT = 24
PADDING = 12

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


class ControlWindow:
    def __init__(self, help_lines: list[str], video_size: tuple[int, int] | None = None) -> None:
        self.video_enabled = video_size is not None
        self.size = video_size or STATUS_ONLY_SIZE
        self._screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Controle do robô")
        pygame.font.init()
        self._font = pygame.font.Font(None, 22)
        self._help = help_lines
        self._status_key: tuple | None = None
        self._panel: pygame.Surface | None = None
        self._frame: pygame.Surface | None = None
        self._frame_array = None  # mantém viva a memória usada pelo frombuffer
        self._dirty = True

    def set_status(
        self,
        connected: bool,
        server: str,
        joystick_name: str | None,
        state: protocol.ControlState,
        video_connected: bool | None = None,
    ) -> None:
        key = (connected, server, joystick_name, state, video_connected)
        if key == self._status_key:
            return
        self._status_key = key
        lines = [
            (f"Robô: conectado a {server}" if connected else f"Robô: sem conexão ({server})",
             OK if connected else WARN),
            (f"Joystick: {joystick_name}" if joystick_name else "Joystick: nenhum", TEXT),
            (f"Comando: {describe_state(state)}", TEXT),
            *((line, MUTED) for line in self._help),
        ]
        if video_connected is not None:
            lines.insert(1, ("Vídeo: recebendo" if video_connected else "Vídeo: sem sinal",
                             OK if video_connected else WARN))
        self._panel = self._render_panel(lines)
        self._dirty = True

    def set_frame(self, frame) -> None:
        """Recebe um quadro BGR (numpy) já no tamanho de exibição."""
        height, width = frame.shape[:2]
        self._frame_array = frame
        self._frame = pygame.image.frombuffer(frame, (width, height), "BGR")
        self._dirty = True

    def draw(self, force: bool = False) -> bool:
        """Redesenha só se algo mudou. Retorna True se desenhou."""
        if not (self._dirty or force):
            return False
        self._screen.fill(BACKGROUND)
        if self._frame is not None:
            # Centraliza (faixas pretas quando a proporção do vídeo difere da janela)
            x = (self.size[0] - self._frame.get_width()) // 2
            y = (self.size[1] - self._frame.get_height()) // 2
            self._screen.blit(self._frame, (x, y))
        elif self.video_enabled:
            waiting = self._font.render("Aguardando vídeo...", True, MUTED)
            self._screen.blit(waiting, waiting.get_rect(center=(self.size[0] // 2, self.size[1] // 3)))
        if self._panel is not None:
            # Painel no rodapé quando há vídeo; no topo na janela só de status
            y = self.size[1] - self._panel.get_height() if self.video_enabled else 0
            self._screen.blit(self._panel, (0, y))
        pygame.display.flip()
        self._dirty = False
        return True

    def _render_panel(self, lines: list[tuple[str, tuple[int, int, int]]]) -> pygame.Surface:
        height = PADDING * 2 + LINE_HEIGHT * len(lines) - (LINE_HEIGHT - 16)
        panel = pygame.Surface((self.size[0], height), pygame.SRCALPHA)
        if self.video_enabled:
            panel.fill(PANEL)
        y = PADDING
        for text, color in lines:
            panel.blit(self._font.render(text, True, color), (PADDING, y))
            y += LINE_HEIGHT
        # Mesmo formato da tela: o blit a cada quadro fica mais barato
        return panel.convert_alpha()
