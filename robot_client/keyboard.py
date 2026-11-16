"""Controle do robô pelo teclado.

O pygame só recebe o teclado com uma janela própria em foco, por isso o
controle por teclado vem junto com a janela de status (status_window.py).
Ao perder o foco o SDL zera o estado das teclas, então o robô para sozinho.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from . import protocol


@dataclass(frozen=True)
class KeyMap:
    forward: tuple[int, ...]
    backward: tuple[int, ...]
    left: tuple[int, ...]
    right: tuple[int, ...]
    camera_up: tuple[int, ...]
    camera_down: tuple[int, ...]
    camera_left: tuple[int, ...]
    camera_right: tuple[int, ...]

    @classmethod
    def from_names(cls, names: dict[str, tuple[str, ...]]) -> KeyMap:
        """Converte nomes de teclas (ex.: "w", "up") em códigos do pygame."""

        def codes(key: str) -> tuple[int, ...]:
            result = []
            for name in names[key]:
                try:
                    result.append(pygame.key.key_code(name))
                except ValueError:
                    raise ValueError(f"{key}: tecla desconhecida {name!r}") from None
            return tuple(result)

        return cls(
            forward=codes("KEY_FORWARD"),
            backward=codes("KEY_BACKWARD"),
            left=codes("KEY_LEFT"),
            right=codes("KEY_RIGHT"),
            camera_up=codes("KEY_CAMERA_UP"),
            camera_down=codes("KEY_CAMERA_DOWN"),
            camera_left=codes("KEY_CAMERA_LEFT"),
            camera_right=codes("KEY_CAMERA_RIGHT"),
        )


def read_keyboard(pressed, keymap: KeyMap) -> protocol.ControlState:
    """Monta o estado a partir das teclas pressionadas (`pygame.key.get_pressed()`)."""

    def held(codes: tuple[int, ...]) -> bool:
        return any(pressed[code] for code in codes)

    flags = 0
    if held(keymap.forward):
        flags |= protocol.FORWARD
    if held(keymap.backward):
        flags |= protocol.BACKWARD
    if held(keymap.left):
        flags |= protocol.LEFT
    if held(keymap.right):
        flags |= protocol.RIGHT
    # Mesmo sentido do analógico: para cima é negativo, para a direita é positivo
    camera_v = held(keymap.camera_down) - held(keymap.camera_up)
    camera_h = held(keymap.camera_right) - held(keymap.camera_left)
    return protocol.ControlState(flags, camera_v, camera_h)


def merge_states(a: protocol.ControlState, b: protocol.ControlState) -> protocol.ControlState:
    """Combina joystick e teclado: movimentos somam; na câmera vale o primeiro ativo."""
    return protocol.ControlState(a.flags | b.flags, a.camera_v or b.camera_v, a.camera_h or b.camera_h)


def keymap_help(names: dict[str, tuple[str, ...]]) -> list[str]:
    """Linhas de ajuda com as teclas configuradas."""

    def fmt(key: str) -> str:
        return "/".join(name.upper() if len(name) == 1 else name for name in names[key])

    return [
        f"Mover: frente {fmt('KEY_FORWARD')}  ré {fmt('KEY_BACKWARD')}  "
        f"esq. {fmt('KEY_LEFT')}  dir. {fmt('KEY_RIGHT')}",
        f"Câmera: cima {fmt('KEY_CAMERA_UP')}  baixo {fmt('KEY_CAMERA_DOWN')}  "
        f"esq. {fmt('KEY_CAMERA_LEFT')}  dir. {fmt('KEY_CAMERA_RIGHT')}  ·  Esc sai",
    ]
