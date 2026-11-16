"""Loop principal: lê o joystick e envia o estado ao robô."""

from __future__ import annotations

import time

import pygame

from . import protocol
from .connection import RobotConnection
from .joystick import JoystickDevice, StateReader, init_pygame
from .settings import Settings


def run_controller(settings: Settings) -> None:
    if not settings.server_host:
        raise SystemExit("Defina SERVER_HOST no arquivo .env")

    init_pygame()
    device = JoystickDevice(settings.joystick_index)
    if not device.connected:
        print("Aguardando joystick...")
    reader = StateReader(settings.bindings, settings.axis_threshold)
    connection = RobotConnection(settings.server_host, settings.server_port)

    heartbeat = settings.heartbeat_s
    last_sent: protocol.ControlState | None = None
    last_send_time = 0.0

    try:
        while True:
            # Bloqueia até chegar um evento ou vencer o heartbeat: sem polling
            wait_ms = max(1, int((last_send_time + heartbeat - time.monotonic()) * 1000))
            events = [pygame.event.wait(wait_ms), *pygame.event.get()]
            for event in events:
                if event.type == pygame.QUIT:
                    return
                device.handle_event(event)

            state = reader.read(device.joystick)
            now = time.monotonic()
            if state != last_sent or now - last_send_time >= heartbeat:
                # Em caso de falha, last_sent=None força o reenvio no próximo ciclo
                last_sent = state if connection.send(protocol.encode(state)) else None
                last_send_time = now
    finally:
        # Tenta parar o robô antes de sair
        if connection.connected:
            connection.send(protocol.encode(protocol.ControlState()))
        connection.close()
        pygame.quit()
