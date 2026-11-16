import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from robot_client.settings import FACE_CASCADE_FILE  # noqa: E402
from robot_client.video import _detect_faces  # noqa: E402


@pytest.fixture(scope="module")
def classifier():
    assert hasattr(cv2, "CascadeClassifier"), "instale opencv-contrib-python (OpenCV 5 removeu do pacote base)"
    clf = cv2.CascadeClassifier(str(FACE_CASCADE_FILE))
    assert not clf.empty(), f"falha ao carregar {FACE_CASCADE_FILE}"
    return clf


def test_cascade_file_exists():
    assert FACE_CASCADE_FILE.is_file()


def test_blank_frame_has_no_faces(classifier):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    assert _detect_faces(cv2, classifier, frame) == []


def test_detections_are_scaled_back_to_frame():
    class FakeClassifier:
        def detectMultiScale(self, gray, scaleFactor, minSize):
            # imagem reduzida pela metade
            assert gray.shape == (240, 320)
            assert minSize == (50, 50)
            return [(10, 20, 30, 40)]

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    assert _detect_faces(cv2, FakeClassifier(), frame) == [(20, 40, 60, 80)]
