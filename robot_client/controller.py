"""Loop principal: lê joystick e teclado, envia o estado ao robô e mostra o vídeo."""

from __future__ import annotations

import time

import pygame

from . import protocol
from .connection import RobotConnection
from .control_window import SHUTDOWN_CONFIRM, SHUTDOWN_IDLE, SHUTDOWN_SENT, ControlWindow
from .joystick import JoystickDevice, StateReader, init_pygame
from .keyboard import KeyMap, keymap_help, merge_states, read_keyboard
from .settings import FACE_CASCADE_FILE, Settings

# Evento postado pela thread de vídeo a cada quadro novo (acorda o loop)
FRAME_EVENT = pygame.event.custom_type()
# Tempo para o segundo clique confirmar o desligamento
SHUTDOWN_CONFIRM_S = 3.0


def _post_frame_event() -> None:
    try:
        pygame.event.post(pygame.event.Event(FRAME_EVENT))
    except pygame.error:
        pass  # pygame já encerrado durante a saída


def run_controller(settings: Settings) -> None:
    if not settings.server_host:
        raise SystemExit("Defina SERVER_HOST no arquivo .env")
    if not settings.bindings_complete and not settings.keyboard_enabled:
        raise SystemExit("Configure o joystick (--configure) ou habilite KEYBOARD_ENABLED")

    video_enabled = settings.video_enabled and bool(settings.streaming_url)
    if settings.video_enabled and not settings.streaming_url:
        print("Defina STREAMING_URL no arquivo .env para exibir o vídeo")
    has_window = settings.keyboard_enabled or video_enabled
    init_pygame(window=has_window, extra_events=(FRAME_EVENT,))

    # Joystick só é usado se estiver mapeado
    reader: StateReader | None = None
    device: JoystickDevice | None = None
    if settings.bindings_complete:
        reader = StateReader(settings.bindings, settings.axis_threshold)
        device = JoystickDevice(settings.joystick_index)
        if not device.connected:
            print("Aguardando joystick...")

    keymap: KeyMap | None = None
    if settings.keyboard_enabled:
        keymap = KeyMap.from_names(settings.key_bindings)
        print("Controle pelo teclado: mantenha a janela 'Controle do robô' em foco")

    window: ControlWindow | None = None
    if has_window:
        help_lines = keymap_help(settings.key_bindings) if keymap is not None else ["Esc sai"]
        window = ControlWindow(help_lines, settings.video_size if video_enabled else None)

    feed = None
    if video_enabled:
        from .video import VideoFeed  # importa o OpenCV só quando há vídeo

        feed = VideoFeed(
            settings.streaming_url,
            window.size,
            settings.video_rotate_180,
            str(FACE_CASCADE_FILE) if settings.face_detection else None,
            on_frame=_post_frame_event,
        )
        feed.start()

    server = f"{settings.server_host}:{settings.server_port}"
    connection = RobotConnection(settings.server_host, settings.server_port)

    heartbeat = settings.heartbeat_s
    last_sent: protocol.ControlState | None = None
    last_send_time = 0.0
    shown_frame_id = 0
    shutdown_state = SHUTDOWN_IDLE
    confirm_deadline = 0.0
    shutdown_lost_connection = False

    try:
        while True:
            # Bloqueia até chegar um evento (joystick, teclado, quadro) ou vencer o heartbeat
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
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and window is not None
                    and window.button_hit(event.pos)
                    and connection.connected
                ):
                    if shutdown_state == SHUTDOWN_IDLE:
                        shutdown_state = SHUTDOWN_CONFIRM
                        confirm_deadline = time.monotonic() + SHUTDOWN_CONFIRM_S
                    elif shutdown_state == SHUTDOWN_CONFIRM:
                        if connection.send(protocol.encode_command(protocol.SHUTDOWN)):
                            print("Desligamento do robô enviado")
                            shutdown_state = SHUTDOWN_SENT
                        else:
                            shutdown_state = SHUTDOWN_IDLE
                if device is not None:
                    device.handle_event(event)

            state = protocol.ControlState()
            if reader is not None:
                state = reader.read(device.joystick)
            if keymap is not None:
                state = merge_states(state, read_keyboard(pygame.key.get_pressed(), keymap))

            now = time.monotonic()
            if shutdown_state == SHUTDOWN_CONFIRM and now >= confirm_deadline:
                shutdown_state = SHUTDOWN_IDLE  # não confirmou a tempo
            elif shutdown_state == SHUTDOWN_SENT:
                # Depois que o robô cai e volta (religado), o botão volta ao normal
                if not connection.connected:
                    shutdown_lost_connection = True
                elif shutdown_lost_connection:
                    shutdown_state = SHUTDOWN_IDLE
                    shutdown_lost_connection = False
            if state != last_sent or now - last_send_time >= heartbeat:
                # Em caso de falha, last_sent=None força o reenvio no próximo ciclo
                last_sent = state if connection.send(protocol.encode(state)) else None
                last_send_time = now

            if window is not None:
                if feed is not None:
                    # Vários avisos acumulados resultam em um só desenho do quadro mais novo
                    frame_id, frame = feed.latest()
                    if frame is not None and frame_id != shown_frame_id:
                        shown_frame_id = frame_id
                        window.set_frame(frame)
                joystick = device.joystick if device is not None else None
                window.set_status(
                    connection.connected,
                    server,
                    joystick.get_name() if joystick is not None else None,
                    state,
                    feed.connected if feed is not None else None,
                )
                window.set_shutdown_button(shutdown_state, connection.connected)
                window.draw(force=redraw)
    finally:
        if feed is not None:
            feed.stop()
        # Tenta parar o robô antes de sair
        if connection.connected:
            connection.send(protocol.encode(protocol.ControlState()))
        connection.close()
        pygame.quit()
