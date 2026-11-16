from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

# Sem janela/áudio reais: permite rodar o pygame no CI (Linux sem display)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robot_client import settings as settings_module  # noqa: E402

_ENV_PREFIXES = (
    "JOYSTICK_", "SERVER_", "SOCKET_", "AXIS_", "SENSIBILIDADE_", "HEARTBEAT_",
    "VIDEO_", "STREAMING_", "RESOLUCAO", "FACE_",
)


@pytest.fixture
def env_file(monkeypatch, tmp_path) -> Path:
    """Isola as configurações: limpa variáveis e aponta o .env para um arquivo temporário."""
    snapshot = dict(os.environ)
    for key in list(os.environ):
        if key.startswith(_ENV_PREFIXES):
            del os.environ[key]
    path = tmp_path / ".env"
    monkeypatch.setattr(settings_module, "ENV_FILE", path)
    yield path
    # save_bindings escreve direto em os.environ; restaura tudo
    os.environ.clear()
    os.environ.update(snapshot)


class FakeJoystick:
    def __init__(self, axes=(), buttons=()) -> None:
        self.axes = list(axes)
        self.buttons = list(buttons)

    def get_numaxes(self) -> int:
        return len(self.axes)

    def get_numbuttons(self) -> int:
        return len(self.buttons)

    def get_axis(self, index: int) -> float:
        return self.axes[index]

    def get_button(self, index: int) -> int:
        return self.buttons[index]


@pytest.fixture
def wait():
    def wait_until(condition, timeout: float = 2.0, interval: float = 0.005) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if condition():
                return True
            time.sleep(interval)
        return condition()

    return wait_until
