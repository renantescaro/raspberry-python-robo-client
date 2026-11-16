import numpy as np
import pygame
import pytest

from robot_client import protocol
from robot_client.control_window import STATUS_ONLY_SIZE, ControlWindow, describe_state
from robot_client.keyboard import keymap_help
from robot_client.settings import DEFAULT_KEYS

HELP = keymap_help(DEFAULT_KEYS)
STATE = protocol.ControlState(protocol.FORWARD, 0, 0)


@pytest.fixture(autouse=True)
def pygame_display():
    pygame.display.init()
    yield
    pygame.display.quit()


def solid_bgr(width: int, height: int, bgr: tuple[int, int, int]) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = bgr
    return frame


@pytest.mark.parametrize(
    ("state", "text"),
    [
        (protocol.ControlState(), "parado"),
        (protocol.ControlState(protocol.FORWARD | protocol.LEFT, 0, 0), "frente + esquerda"),
        (protocol.ControlState(0, -1, 1), "câmera cima/direita"),
        (protocol.ControlState(protocol.BACKWARD, 1, 0), "ré + câmera baixo"),
    ],
)
def test_describe_state(state, text):
    assert describe_state(state) == text


def test_status_only_window():
    window = ControlWindow(HELP)
    assert window.size == STATUS_ONLY_SIZE
    assert pygame.display.get_surface().get_size() == STATUS_ONLY_SIZE
    assert pygame.display.get_caption()[0] == "Controle do robô"


def test_video_window_uses_video_size():
    window = ControlWindow(HELP, (640, 360))
    assert window.size == (640, 360)
    assert pygame.display.get_surface().get_size() == (640, 360)


def test_draws_only_when_something_changes():
    window = ControlWindow(HELP)
    window.set_status(True, "robo:5001", "Gamepad", STATE)
    assert window.draw()
    assert not window.draw()  # nada mudou
    window.set_status(True, "robo:5001", "Gamepad", STATE)
    assert not window.draw()  # mesmo status
    window.set_status(False, "robo:5001", "Gamepad", STATE)
    assert window.draw()
    assert window.draw(force=True)


def test_frame_is_shown_with_correct_colors():
    window = ControlWindow(HELP, (320, 240))
    window.set_status(True, "robo:5001", None, STATE, video_connected=True)
    window.set_frame(solid_bgr(320, 240, (255, 0, 0)))  # azul em BGR
    assert window.draw()
    # Acima do painel de status, o pixel deve ser azul (BGR convertido certo)
    assert pygame.display.get_surface().get_at((60, 20))[:3] == (0, 0, 255)  # fora do botão


def test_smaller_frame_is_centered_with_black_bars():
    window = ControlWindow(HELP, (400, 240))
    window.set_frame(solid_bgr(320, 240, (0, 255, 0)))  # 4:3 numa janela mais larga
    window.draw()
    screen = pygame.display.get_surface()
    assert screen.get_at((200, 20))[:3] == (0, 255, 0)  # centro: vídeo
    assert screen.get_at((10, 20))[:3] != (0, 255, 0)  # faixa lateral
    assert screen.get_at((390, 20))[:3] != (0, 255, 0)


def test_new_frame_marks_window_dirty():
    window = ControlWindow(HELP, (160, 120))
    window.set_frame(solid_bgr(160, 120, (0, 0, 255)))
    assert window.draw()
    assert not window.draw()
    window.set_frame(solid_bgr(160, 120, (255, 255, 255)))
    assert window.draw()


def test_status_panel_overlays_bottom_of_video():
    window = ControlWindow(HELP, (320, 240))
    window.set_frame(solid_bgr(320, 240, (255, 255, 255)))
    window.set_status(True, "robo:5001", None, STATE, video_connected=True)
    window.draw()
    screen = pygame.display.get_surface()
    top = screen.get_at((300, 5))[:3]
    bottom = screen.get_at((300, 235))[:3]
    assert top == (255, 255, 255)
    assert sum(bottom) < sum(top)  # painel translúcido escurece o rodapé


# ---------------------------------------------------------------- botão desligar

from robot_client.control_window import (  # noqa: E402
    SHUTDOWN_CONFIRM,
    SHUTDOWN_IDLE,
    SHUTDOWN_SENT,
)


def test_button_is_in_top_right_corner():
    window = ControlWindow(HELP, (640, 360))
    rect = window.button_rect
    assert rect.right <= 640 and rect.right > 600
    assert rect.top < 20
    assert window.button_hit(rect.center)
    assert not window.button_hit((10, 10))


def button_color(window: ControlWindow):
    # Canto interno do botão (fora do texto)
    return pygame.display.get_surface().get_at((window.button_rect.left + 4, window.button_rect.centery))[:3]


def test_button_states_change_color():
    window = ControlWindow(HELP)
    window.set_shutdown_button(SHUTDOWN_IDLE, True)
    window.draw(force=True)
    idle = button_color(window)
    window.set_shutdown_button(SHUTDOWN_CONFIRM, True)
    assert window.draw()  # mudança de estado redesenha
    confirm = button_color(window)
    assert confirm == (200, 50, 50)  # vermelho de confirmação
    window.set_shutdown_button(SHUTDOWN_SENT, True)
    window.draw()
    assert button_color(window) not in (idle, confirm)


def test_button_disabled_without_connection():
    window = ControlWindow(HELP)
    window.set_shutdown_button(SHUTDOWN_IDLE, True)
    window.draw(force=True)
    enabled = button_color(window)
    window.set_shutdown_button(SHUTDOWN_IDLE, False)
    assert window.draw()
    assert button_color(window) != enabled


def test_same_button_state_does_not_redraw():
    window = ControlWindow(HELP)
    window.set_shutdown_button(SHUTDOWN_IDLE, True)
    window.draw(force=True)
    window.set_shutdown_button(SHUTDOWN_IDLE, True)
    assert not window.draw()
