"""Loop principal: lê joystick e teclado e envia o estado ao robô."""

from __future__ import annotations

import time

import pygame

from . import protocol
from .connection import RobotConnection
from .joystick import JoystickDevice, StateReader, init_pygame
from .keyboard import KeyMap, keymap_help, merge_states, read_keyboard
from .settings import Settings
from .status_window import StatusWindow


def run_controller(settings: Settings) -> None:
    if not settings.server_host:
        raise SystemExit("Defina SERVER_HOST no arquivo .env")
    if not settings.bindings_complete and not settings.keyboard_enabled:
        raise SystemExit("Configure o joystick (--configure) ou habilite KEYBOARD_ENABLED")

    init_pygame(keyboard=settings.keyboard_enabled)

    # Joystick só é usado se estiver mapeado
    reader: StateReader | None = None
    device: JoystickDevice | None = None
    if settings.bindings_complete:
        reader = StateReader(settings.bindings, settings.axis_threshold)
        device = JoystickDevice(settings.joystick_index)
        if not device.connected:
            print("Aguardando joystick...")

    keymap: KeyMap | None = None
    window: StatusWindow | None = None
    if settings.keyboard_enabled:
        keymap = KeyMap.from_names(settings.key_bindings)
        window = StatusWindow(keymap_help(settings.key_bindings))
        print("Controle pelo teclado: mantenha a janela 'Controle do robô' em foco")

    server = f"{settings.server_host}:{settings.server_port}"
    connection = RobotConnection(settings.server_host, settings.server_port)

    heartbeat = settings.heartbeat_s
    last_sent: protocol.ControlState | None = None
    last_send_time = 0.0

    try:
        while True:
            # Bloqueia até chegar um evento ou vencer o heartbeat: sem polling
            wait_ms = max(1, int((last_send_time + heartbeat - time.monotonic()) * 1000))
            events = [pygame.event.wait(wait_ms), *pygame.event.get()]
            redraw = False
            for event in events:
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                if event.type == pygame.WINDOWEXPOSED:
                    redraw = True
                if device is not None:
                    device.handle_event(event)

            state = protocol.ControlState()
            if reader is not None:
                state = reader.read(device.joystick)
            if keymap is not None:
                state = merge_states(state, read_keyboard(pygame.key.get_pressed(), keymap))

            now = time.monotonic()
            if state != last_sent or now - last_send_time >= heartbeat:
                # Em caso de falha, last_sent=None força o reenvio no próximo ciclo
                last_sent = state if connection.send(protocol.encode(state)) else None
                last_send_time = now

            if window is not None:
                joystick = device.joystick if device is not None else None
                window.update(
                    connection.connected,
                    server,
                    joystick.get_name() if joystick is not None else None,
                    state,
                    force=redraw,
                )
    finally:
        # Tenta parar o robô antes de sair
        if connection.connected:
            connection.send(protocol.encode(protocol.ControlState()))
        connection.close()
        pygame.quit()
