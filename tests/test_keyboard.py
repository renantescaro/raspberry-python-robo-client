import pygame
import pytest

from robot_client import protocol
from robot_client.keyboard import KeyMap, keymap_help, merge_states, read_keyboard
from robot_client.settings import DEFAULT_KEYS


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.display.init()
    yield
    pygame.display.quit()


class Pressed:
    """Imita o retorno de pygame.key.get_pressed()."""

    def __init__(self, *keys: int) -> None:
        self.keys = set(keys)

    def __getitem__(self, code: int) -> bool:
        return code in self.keys


@pytest.fixture
def keymap() -> KeyMap:
    return KeyMap.from_names(DEFAULT_KEYS)


def test_default_keymap(keymap):
    assert keymap.forward == (pygame.K_w,)
    assert keymap.left == (pygame.K_a,)
    assert keymap.camera_up == (pygame.K_UP,)


def test_unknown_key_name():
    names = {**DEFAULT_KEYS, "KEY_LEFT": ("tecla-que-nao-existe",)}
    with pytest.raises(ValueError, match="KEY_LEFT"):
        KeyMap.from_names(names)


def test_nothing_pressed(keymap):
    assert read_keyboard(Pressed(), keymap) == protocol.ControlState()


@pytest.mark.parametrize(
    ("keys", "flags"),
    [
        ((pygame.K_w,), protocol.FORWARD),
        ((pygame.K_s,), protocol.BACKWARD),
        ((pygame.K_a,), protocol.LEFT),
        ((pygame.K_d,), protocol.RIGHT),
        ((pygame.K_UP,), 0),  # setas movem só a câmera
        ((pygame.K_w, pygame.K_a), protocol.FORWARD | protocol.LEFT),
    ],
)
def test_movement_keys(keymap, keys, flags):
    assert read_keyboard(Pressed(*keys), keymap).flags == flags


@pytest.mark.parametrize(
    ("keys", "camera"),
    [
        ((pygame.K_UP,), (-1, 0)),  # cima = negativo, igual ao analógico
        ((pygame.K_DOWN,), (1, 0)),
        ((pygame.K_LEFT,), (0, -1)),
        ((pygame.K_RIGHT,), (0, 1)),
        ((pygame.K_UP, pygame.K_DOWN), (0, 0)),  # opostos se anulam
        ((pygame.K_UP, pygame.K_RIGHT), (-1, 1)),
    ],
)
def test_camera_keys(keymap, keys, camera):
    state = read_keyboard(Pressed(*keys), keymap)
    assert (state.camera_v, state.camera_h) == camera
    assert state.flags == 0


def test_custom_keymap():
    names = {**DEFAULT_KEYS, "KEY_FORWARD": ("t", "left shift")}
    keymap = KeyMap.from_names(names)
    assert read_keyboard(Pressed(pygame.K_LSHIFT), keymap).flags == protocol.FORWARD
    assert read_keyboard(Pressed(pygame.K_w), keymap).flags == 0


@pytest.mark.parametrize(
    ("joystick", "keyboard", "expected"),
    [
        ((protocol.FORWARD, 0, 0), (protocol.LEFT, 0, 0), (protocol.FORWARD | protocol.LEFT, 0, 0)),
        ((0, 1, 0), (0, -1, 1), (0, 1, 1)),  # câmera: joystick tem prioridade
        ((0, 0, 0), (0, -1, -1), (0, -1, -1)),
        ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
    ],
)
def test_merge_states(joystick, keyboard, expected):
    merged = merge_states(protocol.ControlState(*joystick), protocol.ControlState(*keyboard))
    assert merged == protocol.ControlState(*expected)


def test_keymap_help_lists_configured_keys():
    lines = keymap_help(DEFAULT_KEYS)
    assert "frente W  ré S  esq. A  dir. D" in lines[0]
    assert lines[1] == "Câmera: setas do teclado  ·  Esc sai"


def test_keymap_help_lists_custom_camera_keys():
    names = {**DEFAULT_KEYS, "KEY_CAMERA_UP": ("i", "up")}
    assert "Câmera: cima I/up  baixo down" in keymap_help(names)[1]
