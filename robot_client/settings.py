"""Configurações do cliente, lidas do arquivo .env na raiz do projeto."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv, set_key

from .bindings import CONTROLS, Binding

PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_DIR / ".env"
FACE_CASCADE_FILE = PROJECT_DIR / "assets" / "haarcascade_face.xml"
# Baixado na primeira vez que a detecção de pessoas/animais é usada (fora do git)
YOLO_MODEL_FILE = PROJECT_DIR / "assets" / "yolo11n.onnx"

# O que pode ser detectado no vídeo (DETECT=face,cat,dog)
DETECTION_TARGETS = ("face", "person", "cat", "dog")

# Nomes antigos (em português) continuam aceitos para não quebrar .env existentes
_LEGACY_KEYS = {
    "SERVER_HOST": "SOCKET_IP",
    "SERVER_PORT": "SOCKET_PORTA",
    "AXIS_THRESHOLD": "SENSIBILIDADE_ANALOGICOS",
    "VIDEO_SIZE": "RESOLUCAO",
    **{control.key: control.legacy_key for control in CONTROLS},
}


def _raw(key: str) -> str | None:
    value = os.getenv(key)
    if value is None and key in _LEGACY_KEYS:
        value = os.getenv(_LEGACY_KEYS[key])
    if value is None or not value.strip():
        return None
    return value.strip()


def _bool(key: str, default: bool) -> bool:
    value = _raw(key)
    return default if value is None else value.lower() in {"1", "true", "yes", "on", "sim"}


def _size(key: str, default: tuple[int, int]) -> tuple[int, int]:
    value = _raw(key)
    if value is None:
        return default
    width, _, height = value.lower().partition("x")
    return int(width), int(height)


# Teclas padrão (nomes do pygame: "w", "up", "left shift"...). Ficam aqui, e não em
# keyboard.py, para este módulo não depender do pygame.
DEFAULT_KEYS: dict[str, tuple[str, ...]] = {
    # Robô no WASD e câmera nas setas (uma mão em cada)
    "KEY_FORWARD": ("w",),
    "KEY_BACKWARD": ("s",),
    "KEY_LEFT": ("a",),
    "KEY_RIGHT": ("d",),
    "KEY_CAMERA_UP": ("up",),
    "KEY_CAMERA_DOWN": ("down",),
    "KEY_CAMERA_LEFT": ("left",),
    "KEY_CAMERA_RIGHT": ("right",),
}


def _key_names(key: str) -> tuple[str, ...]:
    value = _raw(key)
    if value is None:
        return DEFAULT_KEYS[key]
    return tuple(name.strip().lower() for name in value.split(",") if name.strip())


def _targets() -> tuple[str, ...]:
    value = _raw("DETECT") or ""
    targets = [name.strip().lower() for name in value.split(",") if name.strip()]
    unknown = [name for name in targets if name not in DETECTION_TARGETS]
    if unknown:
        raise ValueError(
            f"DETECT: alvo desconhecido {', '.join(unknown)} (use {', '.join(DETECTION_TARGETS)})"
        )
    # Chave antiga: FACE_DETECTION=true equivale a incluir "face"
    if _bool("FACE_DETECTION", False) and "face" not in targets:
        targets.insert(0, "face")
    return tuple(dict.fromkeys(targets))  # sem repetidos, mantendo a ordem


@dataclass(frozen=True)
class Settings:
    server_host: str | None
    server_port: int
    axis_threshold: float
    heartbeat_s: float
    joystick_index: int
    bindings: dict[str, Binding]

    keyboard_enabled: bool
    key_bindings: dict[str, tuple[str, ...]]

    video_enabled: bool
    streaming_url: str | None
    video_size: tuple[int, int]
    video_rotate_180: bool
    detect: tuple[str, ...]
    detect_confidence: float

    @property
    def bindings_complete(self) -> bool:
        return all(control.key in self.bindings for control in CONTROLS)


def load_settings() -> Settings:
    load_dotenv(ENV_FILE)

    bindings: dict[str, Binding] = {}
    for control in CONTROLS:
        text = _raw(control.key)
        if text:
            bindings[control.key] = Binding.parse(text, control.legacy_direction)

    return Settings(
        server_host=_raw("SERVER_HOST"),
        server_port=int(_raw("SERVER_PORT") or 5001),
        axis_threshold=float(_raw("AXIS_THRESHOLD") or 0.4),
        heartbeat_s=float(_raw("HEARTBEAT_S") or 0.25),
        joystick_index=int(_raw("JOYSTICK_INDEX") or 0),
        bindings=bindings,
        keyboard_enabled=_bool("KEYBOARD_ENABLED", True),
        key_bindings={key: _key_names(key) for key in DEFAULT_KEYS},
        video_enabled=_bool("VIDEO_ENABLED", False),
        streaming_url=_raw("STREAMING_URL"),
        video_size=_size("VIDEO_SIZE", (800, 600)),
        video_rotate_180=_bool("VIDEO_ROTATE_180", True),
        detect=_targets(),
        detect_confidence=float(_raw("DETECT_CONFIDENCE") or 0.5),
    )


def save_bindings(bindings: dict[str, Binding]) -> None:
    """Grava o mapeamento do joystick preservando as demais chaves do .env."""
    ENV_FILE.touch(exist_ok=True)
    for key, binding in bindings.items():
        set_key(str(ENV_FILE), key, str(binding), quote_mode="never")
        os.environ[key] = str(binding)
