"""Mapeamento entre controles do robô e entradas do joystick."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControlKind(Enum):
    DIGITAL = "digital"  # liga/desliga (motores)
    ANALOG = "analog"  # direção -1/0/+1 (câmera); exige um eixo


@dataclass(frozen=True)
class Control:
    key: str  # chave no .env
    label: str  # texto exibido na tela de configuração
    kind: ControlKind
    legacy_key: str  # nome antigo no .env (compatibilidade)
    legacy_direction: int  # sentido do eixo usado pela versão antiga


CONTROLS: tuple[Control, ...] = (
    Control("JOYSTICK_FORWARD", "Acelerar", ControlKind.DIGITAL, "JOYSTICK_ACELERADOR", -1),
    Control("JOYSTICK_BACKWARD", "Ré", ControlKind.DIGITAL, "JOYSTICK_RE", -1),
    Control("JOYSTICK_LEFT", "Esquerda", ControlKind.DIGITAL, "JOYSTICK_ESQUERDA", -1),
    Control("JOYSTICK_RIGHT", "Direita", ControlKind.DIGITAL, "JOYSTICK_DIREITA", 1),
    Control("JOYSTICK_CAMERA_V", "Câmera vertical", ControlKind.ANALOG, "JOYSTICK_CAM_V", 0),
    Control("JOYSTICK_CAMERA_H", "Câmera horizontal", ControlKind.ANALOG, "JOYSTICK_CAM_H", 0),
)

_LEGACY_KINDS = {"botao": "button", "analogico": "axis"}


@dataclass(frozen=True)
class Binding:
    """Entrada do joystick. Formatos: `button:3`, `axis:1:-`, `axis:1:+`, `axis:2`."""

    kind: str  # "button" ou "axis"
    index: int
    # Para eixos: +1/-1 = só aquele sentido aciona; 0 = os dois sentidos
    direction: int = 0

    def __str__(self) -> str:
        if self.kind == "button":
            return f"button:{self.index}"
        if self.direction:
            return f"axis:{self.index}:{'+' if self.direction > 0 else '-'}"
        return f"axis:{self.index}"

    @classmethod
    def parse(cls, text: str, legacy_direction: int = 0) -> Binding:
        text = text.strip()
        # Formato antigo: "analogico-1" / "botao-3"
        if "-" in text and ":" not in text:
            old_kind, _, index = text.partition("-")
            kind = _LEGACY_KINDS.get(old_kind)
            if kind is None:
                raise ValueError(f"mapeamento inválido: {text!r}")
            return cls(kind, int(index), legacy_direction if kind == "axis" else 0)

        parts = text.split(":")
        if parts[0] == "button" and len(parts) == 2:
            return cls("button", int(parts[1]))
        if parts[0] == "axis" and len(parts) in (2, 3):
            direction = 0
            if len(parts) == 3:
                if parts[2] not in ("+", "-"):
                    raise ValueError(f"sentido inválido em {text!r}")
                direction = 1 if parts[2] == "+" else -1
            return cls("axis", int(parts[1]), direction)
        raise ValueError(f"mapeamento inválido: {text!r}")
