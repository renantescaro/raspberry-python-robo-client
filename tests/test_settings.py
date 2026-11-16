import os

import pytest

from robot_client.bindings import Binding
from robot_client.settings import DEFAULT_KEYS, load_settings, save_bindings

LEGACY_ENV = """\
JOYSTICK_ACELERADOR=botao-0
JOYSTICK_RE=botao-2
JOYSTICK_ESQUERDA=analogico-0
JOYSTICK_DIREITA=analogico-0
JOYSTICK_CAM_V=analogico-3
JOYSTICK_CAM_H=analogico-2
SENSIBILIDADE_ANALOGICOS=0.5

RESOLUCAO=1280x720
STREAMING_URL=http://robo:8081/

SOCKET_IP=10.0.0.5
SOCKET_PORTA=5002
"""

NEW_BINDINGS = {
    "JOYSTICK_FORWARD": Binding("button", 0),
    "JOYSTICK_BACKWARD": Binding("button", 1),
    "JOYSTICK_LEFT": Binding("axis", 0, -1),
    "JOYSTICK_RIGHT": Binding("axis", 0, 1),
    "JOYSTICK_CAMERA_V": Binding("axis", 3),
    "JOYSTICK_CAMERA_H": Binding("axis", 2),
}


def test_defaults(env_file):
    s = load_settings()
    assert s.server_host is None
    assert s.server_port == 5001
    assert s.axis_threshold == 0.4
    assert s.heartbeat_s == 0.25
    assert s.video_size == (800, 600)
    assert not s.video_enabled and s.video_rotate_180
    assert s.detect == () and s.detect_confidence == 0.5
    assert s.bindings == {}
    assert not s.bindings_complete


def test_legacy_env_file(env_file):
    env_file.write_text(LEGACY_ENV, encoding="utf-8")
    s = load_settings()
    assert (s.server_host, s.server_port) == ("10.0.0.5", 5002)
    assert s.axis_threshold == 0.5
    assert s.video_size == (1280, 720)
    assert s.streaming_url == "http://robo:8081/"
    assert s.bindings_complete
    assert s.bindings["JOYSTICK_FORWARD"] == Binding("button", 0)
    assert s.bindings["JOYSTICK_LEFT"] == Binding("axis", 0, -1)
    assert s.bindings["JOYSTICK_RIGHT"] == Binding("axis", 0, 1)
    assert s.bindings["JOYSTICK_CAMERA_V"] == Binding("axis", 3, 0)


def test_new_keys_win_over_legacy(env_file):
    env_file.write_text("SOCKET_IP=10.0.0.5\nSERVER_HOST=10.0.0.9\n", encoding="utf-8")
    assert load_settings().server_host == "10.0.0.9"


def test_video_flags(env_file):
    env_file.write_text("VIDEO_ENABLED=true\nVIDEO_ROTATE_180=false\nVIDEO_SIZE=640X480\n")
    s = load_settings()
    assert s.video_enabled and not s.video_rotate_180
    assert s.video_size == (640, 480)


def test_detect_targets(env_file):
    env_file.write_text("DETECT= Cat, dog ,cat\nDETECT_CONFIDENCE=0.3\n", encoding="utf-8")
    s = load_settings()
    assert s.detect == ("cat", "dog")  # normalizado e sem repetidos
    assert s.detect_confidence == 0.3


def test_legacy_face_detection_adds_face(env_file):
    env_file.write_text("FACE_DETECTION=1\nDETECT=dog\n", encoding="utf-8")
    assert load_settings().detect == ("face", "dog")


def test_unknown_detect_target_is_an_error(env_file):
    env_file.write_text("DETECT=cat,unicorn\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unicorn"):
        load_settings()


def test_save_bindings_preserves_other_keys(env_file):
    env_file.write_text("SERVER_HOST=10.0.0.9\nSTREAMING_URL=http://robo/\n", encoding="utf-8")
    save_bindings(NEW_BINDINGS)

    content = env_file.read_text(encoding="utf-8")
    assert "SERVER_HOST=10.0.0.9" in content
    assert "STREAMING_URL=http://robo/" in content

    # Recarrega do zero, como numa nova execução
    for key in NEW_BINDINGS:
        del os.environ[key]
    s = load_settings()
    assert s.bindings == NEW_BINDINGS
    assert s.server_host == "10.0.0.9"


def test_save_bindings_creates_file(env_file):
    assert not env_file.exists()
    save_bindings(NEW_BINDINGS)
    assert env_file.exists()
    assert load_settings().bindings_complete


def test_save_bindings_overwrites_previous_value(env_file):
    env_file.write_text("JOYSTICK_FORWARD=button:9\n", encoding="utf-8")
    save_bindings({"JOYSTICK_FORWARD": Binding("axis", 1, -1)})
    content = env_file.read_text(encoding="utf-8")
    assert "JOYSTICK_FORWARD=axis:1:-" in content
    assert "button:9" not in content


def test_keyboard_defaults(env_file):
    s = load_settings()
    assert s.keyboard_enabled
    assert s.key_bindings["KEY_FORWARD"] == ("w", "up")
    assert s.key_bindings["KEY_CAMERA_RIGHT"] == ("l",)
    assert set(s.key_bindings) == set(DEFAULT_KEYS)


def test_custom_keys(env_file):
    env_file.write_text("KEYBOARD_ENABLED=false\nKEY_FORWARD= T , Left Shift \nKEY_LEFT=q\n", encoding="utf-8")
    s = load_settings()
    assert not s.keyboard_enabled
    assert s.key_bindings["KEY_FORWARD"] == ("t", "left shift")
    assert s.key_bindings["KEY_LEFT"] == ("q",)
    assert s.key_bindings["KEY_RIGHT"] == DEFAULT_KEYS["KEY_RIGHT"]
