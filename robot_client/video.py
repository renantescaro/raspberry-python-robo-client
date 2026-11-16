"""Exibição do streaming de vídeo do robô, com detecção de rostos opcional.

Roda em um processo separado para não competir pelo GIL com o envio de
comandos do joystick.
"""

from __future__ import annotations

import multiprocessing
import threading
import time

WINDOW_NAME = "Video Streaming"
FACE_DETECTION_EVERY_N_FRAMES = 3
FACE_DETECTION_SCALE = 0.5  # detecta em imagem reduzida (bem mais rápido)


class _LatestFrameReader(threading.Thread):
    """Lê o stream continuamente e guarda só o quadro mais recente (menor latência)."""

    def __init__(self, source: str | int) -> None:
        super().__init__(name="video-reader", daemon=True)
        self._source = source
        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self.running = True

    def run(self) -> None:
        import cv2

        while self.running:
            capture = cv2.VideoCapture(self._source)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not capture.isOpened():
                print(f"Não foi possível abrir o vídeo: {self._source}")
                time.sleep(1.0)
                continue
            while self.running:
                ok, frame = capture.read()
                if not ok:
                    print("Stream de vídeo interrompido, reconectando...")
                    break
                with self._lock:
                    self._frame = frame
                    self._frame_id += 1
            capture.release()
            time.sleep(1.0)

    def latest(self) -> tuple[int, object]:
        with self._lock:
            return self._frame_id, self._frame


def run_video(
    source: str,
    size: tuple[int, int],
    rotate_180: bool,
    face_cascade_path: str | None,
) -> None:
    import cv2

    # "0", "1"... = índice de webcam local
    video_source: str | int = int(source) if source.isdigit() else source
    reader = _LatestFrameReader(video_source)
    reader.start()

    classifier = None
    if face_cascade_path:
        classifier = cv2.CascadeClassifier(face_cascade_path)
        if classifier.empty():
            print(f"Classificador não carregado: {face_cascade_path}")
            classifier = None

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, *size)

    shown_id = 0
    frame_count = 0
    faces: list[tuple[int, int, int, int]] = []
    try:
        while True:
            frame_id, frame = reader.latest()
            if frame is not None and frame_id != shown_id:
                shown_id = frame_id
                if rotate_180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                if classifier is not None:
                    if frame_count % FACE_DETECTION_EVERY_N_FRAMES == 0:
                        faces = _detect_faces(cv2, classifier, frame)
                    frame_count += 1
                    for x, y, w, h in faces:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(5) & 0xFF
            if key in (27, ord("q")):
                break
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        reader.running = False
        cv2.destroyAllWindows()


def _detect_faces(cv2, classifier, frame) -> list[tuple[int, int, int, int]]:
    small = cv2.resize(frame, None, fx=FACE_DETECTION_SCALE, fy=FACE_DETECTION_SCALE)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    min_size = int(100 * FACE_DETECTION_SCALE)
    detected = classifier.detectMultiScale(gray, scaleFactor=1.5, minSize=(min_size, min_size))
    inverse = 1 / FACE_DETECTION_SCALE
    return [
        (int(x * inverse), int(y * inverse), int(w * inverse), int(h * inverse))
        for x, y, w, h in detected
    ]


def start_video_process(
    source: str,
    size: tuple[int, int],
    rotate_180: bool,
    face_cascade_path: str | None,
) -> multiprocessing.Process:
    process = multiprocessing.Process(
        target=run_video,
        args=(source, size, rotate_180, face_cascade_path),
        name="video",
        daemon=True,
    )
    process.start()
    return process
