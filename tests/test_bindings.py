import pytest

from robot_client.bindings import CONTROLS, Binding, ControlKind


@pytest.mark.parametrize("text", ["button:0", "button:12", "axis:1:-", "axis:2:+", "axis:4"])
def test_roundtrip(text):
    assert str(Binding.parse(text)) == text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("button:3", Binding("button", 3)),
        ("axis:1:-", Binding("axis", 1, -1)),
        ("axis:1:+", Binding("axis", 1, 1)),
        ("axis:5", Binding("axis", 5, 0)),
        ("  axis:2  ", Binding("axis", 2, 0)),
    ],
)
def test_parse(text, expected):
    assert Binding.parse(text) == expected


@pytest.mark.parametrize(
    ("text", "legacy_direction", "expected"),
    [
        ("analogico-1", -1, Binding("axis", 1, -1)),
        ("analogico-0", 1, Binding("axis", 0, 1)),
        ("analogico-3", 0, Binding("axis", 3, 0)),
        ("botao-5", -1, Binding("button", 5)),  # botão ignora o sentido
    ],
)
def test_parse_legacy_format(text, legacy_direction, expected):
    assert Binding.parse(text, legacy_direction) == expected


@pytest.mark.parametrize("text", ["", "axis", "axis:x", "axis:1:*", "button", "button:1:+", "hat:0", "teclado-1"])
def test_parse_invalid(text):
    with pytest.raises(ValueError):
        Binding.parse(text)


def test_controls_have_unique_keys():
    keys = [control.key for control in CONTROLS]
    assert len(keys) == len(set(keys)) == 6
    assert len({control.legacy_key for control in CONTROLS}) == 6


def test_camera_controls_are_analog():
    analog = {control.key for control in CONTROLS if control.kind is ControlKind.ANALOG}
    assert analog == {"JOYSTICK_CAMERA_V", "JOYSTICK_CAMERA_H"}


def test_legacy_directions_match_previous_version():
    directions = {control.key: control.legacy_direction for control in CONTROLS}
    assert directions["JOYSTICK_FORWARD"] == -1
    assert directions["JOYSTICK_BACKWARD"] == -1
    assert directions["JOYSTICK_LEFT"] == -1
    assert directions["JOYSTICK_RIGHT"] == 1
