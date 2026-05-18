import numpy as np

from domain import Detection, ProcessingSettings, RuntimeStatus
from services.detection_service import DetectionService


class StubDetector:
    def __init__(self):
        self.calls = []

    def predict(self, frame, conf=0.3, imgsz=640):
        self.calls.append((frame, conf, imgsz))
        annotated = frame.copy()
        return annotated, [
            {"class": "defect", "confidence": 0.91, "bbox": [1, 2, 3, 4]},
        ]


class RaisingDetector:
    def predict(self, frame, conf=0.3, imgsz=640):
        raise RuntimeError("model exploded")


def test_detect_normalizes_detector_dicts_to_detections():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    detector = StubDetector()
    service = DetectionService(detector)

    result = service.detect(frame, ProcessingSettings(confidence=0.55, imgsz=320))

    assert detector.calls[0][1:] == (0.55, 320)
    assert isinstance(result.detections[0], Detection)
    assert result.detections[0].class_name == "defect"
    assert result.detections[0].confidence == 0.91
    assert result.error is None


def test_detect_returns_error_result_when_detector_raises():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    service = DetectionService(RaisingDetector())

    result = service.detect(frame, ProcessingSettings())

    assert result.annotated_frame is frame
    assert result.detections == []
    assert "model exploded" in result.error
