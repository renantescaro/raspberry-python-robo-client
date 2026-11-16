import pytest
from conftest import FakeJoystick

from robot_client import protocol
from robot_client.bindings import Binding
from robot_client.joystick import StateReader

BINDINGS = {
    "JOYSTICK_FORWARD": Binding("button", 0),
    "JOYSTICK_BACKWARD": Binding("axis", 5, 1),  # gatilho que repousa em -1
    "JOYSTICK_LEFT": Binding("axis", 0, -1),
    "JOYSTICK_RIGHT": Binding("axis", 0, 1),
    "JOYSTICK_CAMERA_V": Binding("axis", 3),
    "JOYSTICK_CAMERA_H": Binding("axis", 2),
}
REST = [0.0, 0.0, 0.0, 0.0, 0.0, -1.0]


@pytest.fixture
def reader():
    return StateReader(BINDINGS, threshold=0.4)


def joystick(buttons=(0,), **axes):
    values = list(REST)
    for name, value in axes.items():
        values[int(name[1:])] = value
    return FakeJoystick(values, buttons)


def test_no_joystick_means_stop(reader):
    assert reader.read(None) == protocol.ControlState()


def test_at_rest(reader):
    assert reader.read(joystick()) == protocol.ControlState()


def test_button(reader):
    assert reader.read(joystick(buttons=(1,))) == protocol.ControlState(protocol.FORWARD, 0, 0)


@pytest.mark.parametrize(
    ("axes", "flags"),
    [
        ({"a0": -0.9}, protocol.LEFT),
        ({"a0": 0.9}, protocol.RIGHT),
        ({"a0": -0.3}, 0),  # abaixo do limiar
        ({"a0": 0.4}, 0),  # limiar é exclusivo
        ({"a5": 0.9}, protocol.BACKWARD),
        ({"a5": 0.0}, 0),  # gatilho no meio do curso ainda não aciona
    ],
)
def test_directional_axes(reader, axes, flags):
    assert reader.read(joystick(**axes)).flags == flags


@pytest.mark.parametrize(
    ("value", "direction"), [(0.8, 1), (-0.8, -1), (0.2, 0), (-0.2, 0), (0.0, 0)]
)
def test_camera_axes(reader, value, direction):
    state = reader.read(joystick(a3=value, a2=-value))
    assert (state.camera_v, state.camera_h) == (direction, -direction)


def test_combined_state(reader):
    state = reader.read(joystick(buttons=(1,), a0=-1.0, a3=1.0, a2=-1.0))
    assert state == protocol.ControlState(protocol.FORWARD | protocol.LEFT, 1, -1)


def test_bidirectional_digital_axis():
    bindings = {**BINDINGS, "JOYSTICK_FORWARD": Binding("axis", 1)}
    reader = StateReader(bindings, threshold=0.4)
    assert reader.read(joystick(buttons=(0,), a1=0.9)).flags == protocol.FORWARD
    assert reader.read(joystick(buttons=(0,), a1=-0.9)).flags == protocol.FORWARD


def test_binding_missing_on_device_is_ignored(reader):
    # Joystick com menos eixos/botões do que o mapeamento espera
    assert reader.read(FakeJoystick([0.0], [])) == protocol.ControlState()


def test_camera_bound_to_button_is_ignored():
    bindings = {**BINDINGS, "JOYSTICK_CAMERA_V": Binding("button", 0)}
    reader = StateReader(bindings, threshold=0.4)
    assert reader.read(joystick(buttons=(1,))).camera_v == 0
