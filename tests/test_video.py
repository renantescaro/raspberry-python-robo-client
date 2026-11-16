"""Testes do vídeo: VideoFeed lendo um servidor MJPEG local de verdade."""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from robot_client.settings import FACE_CASCADE_FILE  # noqa: E402
from robot_client.video import VideoFeed, _detect_faces, fit_size  # noqa: E402


def make_test_frame():
    """640x480: metade de cima branca, metade de baixo preta."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:240] = 255
    return frame


@pytest.fixture
def mjpeg_server():
    """Servidor MJPEG no mesmo formato do streaming do robô."""
    jpeg = cv2.imencode(".jpg", make_test_frame())[1].tobytes()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()
            try:
                while True:
                    self.wfile.write(
                        b"--FRAME\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n%s\r\n"
                        % (len(jpeg), jpeg)
                    )
                    time.sleep(0.03)
            except OSError:
                pass

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/?action=stream"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def run_feed():
    feeds = []

    def start(url, area=(640, 480), rotate=False, on_frame=None):
        feed = VideoFeed(url, area, rotate, on_frame=on_frame)
        feed.start()
        feeds.append(feed)
        return feed

    yield start
    for feed in feeds:
        feed.stop()
        feed.join(timeout=5)


# ------------------------------------------------------------------- fit_size


@pytest.mark.parametrize(
    ("frame", "area", "expected"),
    [
        ((640, 480), (640, 480), (640, 480)),
        ((640, 480), (1280, 720), (960, 720)),  # 4:3 numa área 16:9
        ((640, 480), (800, 600), (800, 600)),
        ((1280, 720), (640, 480), (640, 360)),
        ((640, 480), (320, 480), (320, 240)),
    ],
)
def test_fit_size_keeps_aspect_ratio(frame, area, expected):
    assert fit_size(frame, area) == expected


# ------------------------------------------------------------------ VideoFeed


def test_reads_mjpeg_stream(mjpeg_server, run_feed, wait):
    calls = []
    feed = run_feed(mjpeg_server, on_frame=lambda: calls.append(1))
    assert wait(lambda: feed.latest()[1] is not None, timeout=10)
    assert feed.connected
    frame_id, frame = feed.latest()
    assert frame.shape == (480, 640, 3)
    assert frame[10, 320].mean() > 200 and frame[470, 320].mean() < 50  # não girado
    assert wait(lambda: feed.latest()[0] > frame_id)  # continua recebendo
    assert calls  # avisou o loop principal


def test_rotates_and_scales_to_area(mjpeg_server, run_feed, wait):
    feed = run_feed(mjpeg_server, area=(1280, 720), rotate=True)
    assert wait(lambda: feed.latest()[1] is not None, timeout=10)
    frame = feed.latest()[1]
    assert frame.shape == (720, 960, 3)  # proporção mantida
    assert frame[10, 480].mean() < 50 and frame[710, 480].mean() > 200  # girado 180°


def test_unreachable_stream_keeps_retrying_and_stops(run_feed, wait):
    feed = run_feed("http://127.0.0.1:9/?action=stream")
    time.sleep(0.3)
    assert feed.latest() == (0, None)
    assert not feed.connected
    feed.stop()
    feed.join(timeout=5)
    assert not feed.is_alive()  # stop() interrompe a espera de reconexão


# ------------------------------------------------------------- detecção de rosto


@pytest.fixture(scope="module")
def classifier():
    assert hasattr(cv2, "CascadeClassifier"), "instale opencv-contrib-python (OpenCV 5 removeu do pacote base)"
    clf = cv2.CascadeClassifier(str(FACE_CASCADE_FILE))
    assert not clf.empty(), f"falha ao carregar {FACE_CASCADE_FILE}"
    return clf


def test_blank_frame_has_no_faces(classifier):
    assert _detect_faces(cv2, classifier, np.zeros((480, 640, 3), dtype=np.uint8)) == []


def test_detections_are_scaled_back_to_frame():
    class FakeClassifier:
        def detectMultiScale(self, gray, scaleFactor, minSize):
            assert gray.shape == (240, 320)  # imagem reduzida pela metade
            assert minSize == (50, 50)
            return [(10, 20, 30, 40)]

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    assert _detect_faces(cv2, FakeClassifier(), frame) == [(20, 40, 60, 80)]
