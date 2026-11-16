"""Leitura do vídeo do robô (MJPEG por HTTP) em uma thread.

A thread lê, decodifica, gira, redimensiona e (opcionalmente) detecta rostos,
pessoas e animais (detection.py).
Essas operações do OpenCV rodam em C e liberam o GIL, então não atrasam o loop
de controle. Só o quadro mais recente é guardado (menor latência possível); a
janela (control_window.py) apenas o desenha.
"""

from __future__ import annotations

import threading
from typing import Callable

# Detecta a cada N quadros; nos intermediários repete as últimas caixas
DETECTION_EVERY_N_FRAMES = 2
RECONNECT_DELAY_S = 1.0
# Limites de abertura/leitura do stream: sem eles uma conexão travada prende a thread
STREAM_TIMEOUT_MS = 3000


def fit_size(frame_size: tuple[int, int], area: tuple[int, int]) -> tuple[int, int]:
    """Maior tamanho que cabe em `area` mantendo a proporção do quadro."""
    width, height = frame_size
    area_w, area_h = area
    scale = min(area_w / width, area_h / height)
    return max(1, round(width * scale)), max(1, round(height * scale))


class VideoFeed(threading.Thread):
    def __init__(
        self,
        source: str,
        area: tuple[int, int],
        rotate_180: bool,
        detector_factory: Callable[[], object | None] | None = None,
        on_frame: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(name="video", daemon=True)
        # "0", "1"... = índice de webcam local
        self._source: str | int = int(source) if source.isdigit() else source
        self._area = area
        self._rotate_180 = rotate_180
        # Chamada já dentro da thread: carregar/baixar o modelo não trava a janela
        self._detector_factory = detector_factory
        self._on_frame = on_frame
        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self._stop_event = threading.Event()
        self.connected = False

    def latest(self) -> tuple[int, object]:
        """Retorna (id, quadro BGR já no tamanho de exibição)."""
        with self._lock:
            return self._frame_id, self._frame

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        import cv2

        detector = self._detector_factory() if self._detector_factory else None
        if detector is not None:
            from .detection import draw_detections
        detections: list = []
        count = 0
        while not self._stop_event.is_set():
            capture = self._open(cv2)
            if not capture.isOpened():
                self._wait_reconnect()
                continue
            while not self._stop_event.is_set():
                ok, frame = capture.read()
                if not ok:
                    break
                self.connected = True
                if self._rotate_180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                if detector is not None:
                    if count % DETECTION_EVERY_N_FRAMES == 0:
                        detections = detector.detect(frame)
                    count += 1
                    draw_detections(frame, detections)
                height, width = frame.shape[:2]
                size = fit_size((width, height), self._area)
                if size != (width, height):
                    frame = cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
                with self._lock:
                    self._frame = frame
                    self._frame_id += 1
                if self._on_frame is not None:
                    self._on_frame()
            capture.release()
            self.connected = False
            if not self._stop_event.is_set():
                self._wait_reconnect()

    def _open(self, cv2):
        if isinstance(self._source, int):
            capture = cv2.VideoCapture(self._source)
        else:
            # URL: FFmpeg direto (sem testar outros backends) e com tempo limite
            capture = cv2.VideoCapture(
                self._source,
                cv2.CAP_FFMPEG,
                [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, STREAM_TIMEOUT_MS,
                 cv2.CAP_PROP_READ_TIMEOUT_MSEC, STREAM_TIMEOUT_MS],
            )
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return capture

    def _wait_reconnect(self) -> None:
        self.connected = False
        self._stop_event.wait(RECONNECT_DELAY_S)  # interrompido na hora por stop()
