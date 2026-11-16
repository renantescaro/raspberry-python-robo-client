"""Ponto de entrada do cliente desktop (Windows / Linux) do robô."""

from __future__ import annotations

import argparse
import sys

from robot_client.settings import FACE_CASCADE_FILE, load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controle do robô via joystick")
    parser.add_argument("--configure", action="store_true", help="abre a tela de mapeamento")
    parser.add_argument(
        "--test-joystick", action="store_true", help="mostra os botões/eixos pressionados"
    )
    parser.add_argument("--video", action="store_true", help="força a exibição do vídeo")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings()

    if args.test_joystick:
        from robot_client.joystick_test import run_joystick_test

        run_joystick_test(settings.joystick_index)
        return 0

    # Sem teclado, o joystick é obrigatório: abre a configuração se faltar mapeamento
    if args.configure or (not settings.bindings_complete and not settings.keyboard_enabled):
        from robot_client.config_gui import run_config

        if not run_config(settings):
            return 0
        settings = load_settings()
    elif not settings.bindings_complete:
        print("Joystick não configurado (use --configure); controlando só pelo teclado.")

    video_process = None
    if (settings.video_enabled or args.video) and settings.streaming_url:
        from robot_client.video import start_video_process

        video_process = start_video_process(
            settings.streaming_url,
            settings.video_size,
            settings.video_rotate_180,
            str(FACE_CASCADE_FILE) if settings.face_detection else None,
        )
    elif args.video:
        print("Defina STREAMING_URL no arquivo .env para exibir o vídeo")

    from robot_client.controller import run_controller

    try:
        run_controller(settings)
    except KeyboardInterrupt:
        pass
    finally:
        if video_process is not None and video_process.is_alive():
            video_process.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
