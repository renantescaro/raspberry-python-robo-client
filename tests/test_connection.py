from __future__ import annotations

import socket

import pytest

from robot_client import connection as connection_module
from robot_client import protocol
from robot_client.connection import RobotConnection


@pytest.fixture
def listener():
    with socket.create_server(("127.0.0.1", 0)) as server:
        server.settimeout(2)
        yield server


def free_port() -> int:
    with socket.create_server(("127.0.0.1", 0)) as server:
        return server.getsockname()[1]


def test_connects_lazily_and_sends(listener):
    conn = RobotConnection(*listener.getsockname())
    assert not conn.connected
    assert conn.send(b"\xa5\x01\x00\x00")
    peer, _ = listener.accept()
    with peer:
        assert peer.recv(4) == b"\xa5\x01\x00\x00"
    conn.close()


def test_enables_tcp_nodelay(listener):
    conn = RobotConnection(*listener.getsockname())
    assert conn.send(b"x")
    assert conn._sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
    conn.close()


def test_unreachable_server_returns_false():
    conn = RobotConnection("127.0.0.1", free_port())
    assert conn.send(b"x") is False
    assert not conn.connected


def test_respects_retry_interval(monkeypatch):
    attempts = []

    def fake_create_connection(address, timeout):
        attempts.append(address)
        raise ConnectionRefusedError

    monkeypatch.setattr(connection_module.socket, "create_connection", fake_create_connection)
    clock = [100.0]
    monkeypatch.setattr(connection_module.time, "monotonic", lambda: clock[0])

    conn = RobotConnection("127.0.0.1", 1, retry_interval_s=1.0)
    conn.send(b"x")
    conn.send(b"x")
    clock[0] += 0.5
    conn.send(b"x")
    assert len(attempts) == 1
    clock[0] += 0.6
    conn.send(b"x")
    assert len(attempts) == 2


def test_reconnects_after_server_drops(listener, wait):
    conn = RobotConnection(*listener.getsockname(), retry_interval_s=0.0)
    assert conn.send(b"a")
    peer, _ = listener.accept()
    peer.close()

    # Após o servidor fechar, algum envio falha e a conexão é descartada
    assert wait(lambda: not conn.send(b"b"))
    assert not conn.connected

    assert conn.send(b"c")
    peer, _ = listener.accept()
    with peer:
        assert peer.recv(1) == b"c"
    conn.close()


def test_close_is_idempotent(listener):
    conn = RobotConnection(*listener.getsockname())
    conn.send(b"x")
    conn.close()
    conn.close()
    assert not conn.connected


def connected_pair(listener) -> tuple[RobotConnection, socket.socket]:
    conn = RobotConnection(*listener.getsockname())
    assert conn.send(b"\xa5\x00\x00\x00")
    peer, _ = listener.accept()
    return conn, peer


def test_receive_without_connection_is_empty():
    assert RobotConnection("127.0.0.1", free_port()).receive() == []


def test_receive_returns_telemetry_and_keeps_partial_packet(listener, wait):
    conn, peer = connected_pair(listener)
    with peer:
        first = protocol.encode_telemetry(protocol.Telemetry(91, -46))
        second = protocol.encode_telemetry(protocol.Telemetry(20, -85))
        peer.sendall(first + second[:2])
        received = []
        assert wait(lambda: received.extend(conn.receive()) or received)
        assert received == [protocol.Telemetry(91, -46)]
        peer.sendall(second[2:])
        assert wait(lambda: received.extend(conn.receive()) or len(received) == 2)
        assert received[1] == protocol.Telemetry(20, -85)
    conn.close()


def test_receive_does_not_block(listener):
    conn, peer = connected_pair(listener)
    with peer:
        assert conn.receive() == []  # nada chegou: volta na hora
        assert conn.connected
    conn.close()


def test_receive_ignores_unknown_packets(listener, wait):
    conn, peer = connected_pair(listener)
    with peer:
        peer.sendall(b"\xee\x01\x02\x03" + protocol.encode_telemetry(protocol.Telemetry(50, -70)))
        received = []
        assert wait(lambda: received.extend(conn.receive()) or received)
        assert received == [protocol.Telemetry(50, -70)]
    conn.close()


def test_receive_detects_server_close(listener, wait):
    conn, peer = connected_pair(listener)
    peer.close()
    assert wait(lambda: conn.receive() == [] and not conn.connected)
