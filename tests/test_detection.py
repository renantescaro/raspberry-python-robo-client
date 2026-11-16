"""Testes da detecção (rostos com Haar, pessoas/animais com YOLO)."""

from __future__ import annotations

import hashlib

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from robot_client import detection  # noqa: E402
from robot_client.detection import (  # noqa: E402
    COCO_CLASSES,
    Detection,
    FaceDetector,
    Letterbox,
    MultiDetector,
    YoloDetector,
    build_detector,
    decode_yolo,
    detect_faces,
    draw_detections,
    ensure_model,
    letterbox,
)
from robot_client.settings import FACE_CASCADE_FILE, YOLO_MODEL_FILE  # noqa: E402

CLASSES = {COCO_CLASSES["cat"]: "cat", COCO_CLASSES["dog"]: "dog"}
HORSE = 17


def blank(width=640, height=480):
    return np.zeros((height, width, 3), dtype=np.uint8)


def yolo_output(*boxes):
    """Saída falsa do YOLO: cada caixa é (cx, cy, w, h, {classe: score})."""
    output = np.zeros((1, 84, len(boxes)), dtype=np.float32)
    for i, (cx, cy, w, h, scores) in enumerate(boxes):
        output[0, :4, i] = (cx, cy, w, h)
        for cls, score in scores.items():
            output[0, 4 + cls, i] = score
    return output


# ------------------------------------------------------------------- rostos


def test_face_cascade_loads_and_finds_nothing_on_blank_frame():
    assert hasattr(cv2, "CascadeClassifier"), "instale opencv-contrib-python (OpenCV 5 removeu do pacote base)"
    assert FaceDetector(FACE_CASCADE_FILE).detect(blank()) == []


def test_missing_cascade_is_an_error(tmp_path):
    with pytest.raises(RuntimeError):
        FaceDetector(tmp_path / "nao-existe.xml")


def test_faces_are_scaled_back_to_frame():
    class FakeClassifier:
        def detectMultiScale(self, gray, scaleFactor, minSize):
            assert gray.shape == (240, 320)  # imagem reduzida pela metade
            assert minSize == (50, 50)
            return [(10, 20, 30, 40)]

    assert detect_faces(FakeClassifier(), blank()) == [(20, 40, 60, 80)]


# ---------------------------------------------------------------- letterbox


def test_letterbox_keeps_aspect_ratio_and_pads():
    frame = np.full((480, 640, 3), 255, dtype=np.uint8)
    padded, info = letterbox(frame, 640)
    assert padded.shape == (640, 640, 3)
    assert info == Letterbox(1.0, 0, 80)
    assert tuple(padded[40, 320]) == (114, 114, 114)  # faixa de cima
    assert tuple(padded[320, 320]) == (255, 255, 255)  # imagem


def test_letterbox_scales_large_frames():
    padded, info = letterbox(blank(1280, 720), 640)
    assert padded.shape == (640, 640, 3)
    assert info.scale == 0.5 and info.pad_x == 0 and info.pad_y == 140


# ----------------------------------------------------------- saída do YOLO


def test_decode_maps_boxes_back_to_frame():
    # Quadro 640x480 no letterbox 640x640: 80 px de faixa em cima
    output = yolo_output((320, 320, 100, 200, {COCO_CLASSES["dog"]: 0.9}))
    found = decode_yolo(output, CLASSES, 0.5, Letterbox(1.0, 0, 80), (640, 480))
    assert found == [Detection("dog", pytest.approx(0.9), (270, 140, 100, 200))]


def test_decode_ignores_low_confidence_and_other_classes():
    output = yolo_output(
        (100, 300, 50, 50, {COCO_CLASSES["cat"]: 0.3}),  # confiança baixa
        (300, 300, 50, 50, {COCO_CLASSES["person"]: 0.95}),  # não é alvo
        # Cavalo com um pouco de "cachorro": a classe principal não é alvo
        (500, 300, 50, 50, {HORSE: 0.8, COCO_CLASSES["dog"]: 0.6}),
    )
    assert decode_yolo(output, CLASSES, 0.5, Letterbox(1.0, 0, 80), (640, 480)) == []


def test_decode_suppresses_overlapping_boxes_per_class():
    output = yolo_output(
        (300, 300, 100, 100, {COCO_CLASSES["dog"]: 0.9}),
        (305, 302, 100, 100, {COCO_CLASSES["dog"]: 0.7}),  # mesma caixa, mais fraca
        (305, 302, 100, 100, {COCO_CLASSES["cat"]: 0.8}),  # outra classe: fica
    )
    found = decode_yolo(output, CLASSES, 0.5, Letterbox(1.0, 0, 80), (640, 480))
    assert sorted((d.target, round(d.confidence, 1)) for d in found) == [("cat", 0.8), ("dog", 0.9)]


def test_decode_clips_boxes_to_frame():
    output = yolo_output((10, 90, 100, 40, {COCO_CLASSES["cat"]: 0.9}))
    (found,) = decode_yolo(output, CLASSES, 0.5, Letterbox(1.0, 0, 80), (640, 480))
    x, y, w, h = found.box
    assert (x, y) == (0, 0) and x + w <= 640 and y + h <= 480


# -------------------------------------------------------------- download


@pytest.fixture
def model_source(tmp_path):
    source = tmp_path / "origem.onnx"
    source.write_bytes(b"modelo de teste")
    return source.as_uri(), hashlib.sha256(b"modelo de teste").hexdigest()


def test_ensure_model_downloads_and_verifies(tmp_path, model_source):
    url, digest = model_source
    target = tmp_path / "assets" / "yolo.onnx"
    assert ensure_model(target, url, digest) == target
    assert target.read_bytes() == b"modelo de teste"


def test_ensure_model_keeps_valid_file(tmp_path, model_source):
    _, digest = model_source
    target = tmp_path / "yolo.onnx"
    target.write_bytes(b"modelo de teste")
    # URL inválida: não pode tentar baixar de novo
    assert ensure_model(target, "file:///nao/existe.onnx", digest) == target


def test_ensure_model_rejects_wrong_hash(tmp_path, model_source):
    url, _ = model_source
    target = tmp_path / "yolo.onnx"
    with pytest.raises(RuntimeError, match="SHA-256"):
        ensure_model(target, url, "0" * 64)
    assert list(tmp_path.glob("yolo.onnx*")) == []  # nada pela metade


def test_ensure_model_replaces_corrupted_file(tmp_path, model_source):
    url, digest = model_source
    target = tmp_path / "yolo.onnx"
    target.write_bytes(b"corrompido")
    ensure_model(target, url, digest)
    assert target.read_bytes() == b"modelo de teste"


# ------------------------------------------------------------- composição


def test_build_detector_without_targets_is_none():
    assert build_detector([], 0.5) is None


def test_build_detector_keeps_faces_when_model_fails(monkeypatch, capsys):
    def offline(*args, **kwargs):
        raise OSError("sem internet")

    monkeypatch.setattr(detection, "ensure_model", offline)
    detector = build_detector(["face", "cat"], 0.5)
    assert isinstance(detector, MultiDetector)
    assert detector.detect(blank()) == []  # só o Haar ficou
    assert "gato desativada: sem internet" in capsys.readouterr().out


def test_build_detector_returns_none_when_everything_fails(monkeypatch):
    monkeypatch.setattr(detection, "ensure_model", lambda: (_ for _ in ()).throw(OSError("x")))
    assert build_detector(["dog"], 0.5) is None


def test_draw_detections_draws_box_and_label():
    frame = blank()
    draw_detections(frame, [Detection("cat", 0.87, (100, 200, 80, 60))])
    assert tuple(frame[230, 100]) == (0, 200, 255)  # borda
    assert tuple(frame[195, 101]) == (0, 200, 255)  # fundo do rótulo, acima da caixa
    assert frame[230, 140].mean() == 0  # interior intacto


# ------------------------------------------------------- modelo de verdade


@pytest.mark.skipif(not YOLO_MODEL_FILE.is_file(), reason="modelo YOLO ainda não baixado")
def test_real_model_runs_and_finds_nothing_on_blank_frame():
    detector = YoloDetector(YOLO_MODEL_FILE, ["person", "cat", "dog"], 0.5)
    assert detector.detect(blank()) == []
