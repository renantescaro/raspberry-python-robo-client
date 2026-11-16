"""Detecção no vídeo: rostos (Haar cascade) e pessoas/animais (YOLO11n).

O YOLO roda pelo módulo DNN do próprio OpenCV (sem PyTorch). O modelo ONNX não
fica no repositório: é baixado na primeira vez para assets/ e conferido pelo
SHA-256. Tudo aqui roda na thread de vídeo, nunca no loop de controle.
"""

from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path
from typing import Iterable, NamedTuple, Protocol

import cv2
import numpy as np

from .settings import FACE_CASCADE_FILE, YOLO_MODEL_FILE

YOLO_MODEL_URL = (
    "https://github.com/renantescaro/raspberry-python-robo-client/"
    "releases/download/modelo-yolo11n/yolo11n.onnx"
)
YOLO_MODEL_SHA256 = "6e300a6013de095f7f871d7cfc0cdcf1ee4575b322ecba99b189300b1a89c554"
YOLO_INPUT_SIZE = 640  # o modelo foi exportado com entrada fixa 640x640
YOLO_NMS_THRESHOLD = 0.45
DOWNLOAD_TIMEOUT_S = 30

# Alvo -> índice da classe no COCO (as classes do YOLO pré-treinado)
COCO_CLASSES = {"person": 0, "cat": 15, "dog": 16}

# Texto exibido (cv2.putText não desenha acentos) e cor BGR de cada alvo
LABELS = {"face": "rosto", "person": "pessoa", "cat": "gato", "dog": "cachorro"}
COLORS = {
    "face": (0, 0, 255),
    "person": (255, 160, 0),
    "cat": (0, 200, 255),
    "dog": (0, 220, 0),
}

FACE_SCALE = 0.5  # o Haar roda em imagem reduzida (bem mais rápido)


class Detection(NamedTuple):
    target: str  # "face", "person", "cat" ou "dog"
    confidence: float | None  # o Haar não informa confiança
    box: tuple[int, int, int, int]  # x, y, largura, altura (pixels do quadro)


class Detector(Protocol):
    def detect(self, frame) -> list[Detection]: ...


# ------------------------------------------------------------------- rostos


class FaceDetector:
    def __init__(self, cascade_path: Path = FACE_CASCADE_FILE) -> None:
        self._classifier = cv2.CascadeClassifier(str(cascade_path))
        if self._classifier.empty():
            raise RuntimeError(f"classificador não carregado: {cascade_path}")

    def detect(self, frame) -> list[Detection]:
        return [Detection("face", None, box) for box in detect_faces(self._classifier, frame)]


def detect_faces(classifier, frame) -> list[tuple[int, int, int, int]]:
    small = cv2.resize(frame, None, fx=FACE_SCALE, fy=FACE_SCALE)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    min_size = int(100 * FACE_SCALE)
    detected = classifier.detectMultiScale(gray, scaleFactor=1.5, minSize=(min_size, min_size))
    inverse = 1 / FACE_SCALE
    return [
        (int(x * inverse), int(y * inverse), int(w * inverse), int(h * inverse))
        for x, y, w, h in detected
    ]


# --------------------------------------------------------------------- YOLO


class Letterbox(NamedTuple):
    """Como o quadro foi encaixado na entrada quadrada do modelo."""

    scale: float
    pad_x: float
    pad_y: float


def letterbox(frame, size: int = YOLO_INPUT_SIZE):
    """Redimensiona mantendo a proporção e completa com cinza (padrão do YOLO)."""
    height, width = frame.shape[:2]
    scale = min(size / width, size / height)
    new_w, new_h = round(width * scale), round(height * scale)
    pad_x, pad_y = (size - new_w) / 2, (size - new_h) / 2
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    top, left = int(pad_y), int(pad_x)
    padded = cv2.copyMakeBorder(
        resized, top, size - new_h - top, left, size - new_w - left,
        cv2.BORDER_CONSTANT, value=(114, 114, 114),
    )
    return padded, Letterbox(scale, left, top)


def decode_yolo(
    output,
    classes: dict[int, str],
    confidence: float,
    box_info: Letterbox,
    frame_size: tuple[int, int],
) -> list[Detection]:
    """Converte a saída (1, 4 + classes, N) do YOLO em detecções no quadro original.

    Só aceita a caixa se a classe mais provável dela for um dos alvos (um
    "cavalo" com 20% de "cachorro" não vira cachorro).
    """
    predictions = output[0].T  # (N, 4 + classes)
    scores = predictions[:, 4:]
    best = scores.argmax(axis=1)
    best_score = scores[np.arange(len(scores)), best]
    keep = np.isin(best, list(classes)) & (best_score >= confidence)
    if not keep.any():
        return []
    cx, cy, w, h = predictions[keep, :4].T
    best, best_score = best[keep], best_score[keep]

    # Desfaz o letterbox e limita ao quadro
    width, height = frame_size
    x1 = np.clip((cx - w / 2 - box_info.pad_x) / box_info.scale, 0, width)
    y1 = np.clip((cy - h / 2 - box_info.pad_y) / box_info.scale, 0, height)
    x2 = np.clip((cx + w / 2 - box_info.pad_x) / box_info.scale, 0, width)
    y2 = np.clip((cy + h / 2 - box_info.pad_y) / box_info.scale, 0, height)
    boxes = np.stack([x1, y1, x2 - x1, y2 - y1], axis=1)

    indices = cv2.dnn.NMSBoxesBatched(
        boxes.tolist(), best_score.tolist(), best.tolist(), confidence, YOLO_NMS_THRESHOLD
    )
    return [
        Detection(
            classes[int(best[i])],
            float(best_score[i]),
            tuple(int(round(v)) for v in boxes[i]),
        )
        for i in np.array(indices).flatten()
    ]


class YoloDetector:
    def __init__(self, model_path: Path, targets: Iterable[str], confidence: float) -> None:
        self._net = cv2.dnn.readNetFromONNX(str(model_path))
        self._classes = {COCO_CLASSES[target]: target for target in targets}
        self._confidence = confidence

    def detect(self, frame) -> list[Detection]:
        padded, box_info = letterbox(frame)
        blob = cv2.dnn.blobFromImage(padded, 1 / 255, swapRB=True)
        self._net.setInput(blob)
        output = self._net.forward()
        height, width = frame.shape[:2]
        return decode_yolo(output, self._classes, self._confidence, box_info, (width, height))


def ensure_model(
    path: Path = YOLO_MODEL_FILE,
    url: str = YOLO_MODEL_URL,
    sha256: str = YOLO_MODEL_SHA256,
) -> Path:
    """Garante o modelo em `path`, baixando se faltar ou estiver corrompido."""
    if path.is_file() and _sha256(path) == sha256:
        return path
    print(f"Baixando o modelo de detecção para {path} ...")
    partial = path.with_name(path.name + ".part")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response, partial.open("wb") as out:
            while chunk := response.read(1 << 16):
                out.write(chunk)
        if _sha256(partial) != sha256:
            raise RuntimeError("SHA-256 do modelo baixado não confere")
        os.replace(partial, path)
    finally:
        partial.unlink(missing_ok=True)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------- composição


class MultiDetector:
    def __init__(self, detectors: list[Detector]) -> None:
        self._detectors = detectors

    def detect(self, frame) -> list[Detection]:
        return [found for detector in self._detectors for found in detector.detect(frame)]


def build_detector(targets: Iterable[str], confidence: float) -> Detector | None:
    """Monta os detectores pedidos. Falhas desativam só a parte afetada."""
    targets = list(targets)
    detectors: list[Detector] = []
    if "face" in targets:
        try:
            detectors.append(FaceDetector())
        except (RuntimeError, cv2.error) as exc:
            print(f"Detecção de rostos desativada: {exc}")
    yolo_targets = [target for target in targets if target in COCO_CLASSES]
    if yolo_targets:
        try:
            detectors.append(YoloDetector(ensure_model(), yolo_targets, confidence))
        except (OSError, RuntimeError, cv2.error) as exc:
            print(f"Detecção de {', '.join(LABELS[t] for t in yolo_targets)} desativada: {exc}")
    return MultiDetector(detectors) if detectors else None


def draw_detections(frame, detections: Iterable[Detection]) -> None:
    for target, confidence, (x, y, w, h) in detections:
        color = COLORS[target]
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        text = LABELS[target] if confidence is None else f"{LABELS[target]} {confidence:.0%}"
        (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        top = max(0, y - text_h - baseline - 4)
        cv2.rectangle(frame, (x, top), (x + text_w + 6, top + text_h + baseline + 4), color, -1)
        cv2.putText(
            frame, text, (x + 3, top + text_h + 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
        )
