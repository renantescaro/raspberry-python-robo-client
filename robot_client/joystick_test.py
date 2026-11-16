"""Mostra no terminal os botões e eixos acionados no joystick."""

from __future__ import annotations

import pygame

from .joystick import JoystickDevice, init_pygame

AXIS_PRINT_THRESHOLD = 0.16


def run_joystick_test(index: int) -> None:
    init_pygame()
    device = JoystickDevice(index)
    if not device.connected:
        print("Aguardando joystick...")
    print("Pressione Ctrl+C para sair.")
    try:
        while True:
            event = pygame.event.wait()
            device.handle_event(event)
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"button:{event.button}")
            elif event.type == pygame.JOYAXISMOTION and abs(event.value) > AXIS_PRINT_THRESHOLD:
                print(f"axis:{event.axis} -> {event.value:+.2f}")
            elif event.type == pygame.JOYHATMOTION:
                print(f"hat:{event.hat} -> {event.value}")
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
