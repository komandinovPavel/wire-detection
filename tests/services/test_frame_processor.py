import numpy as np

from domain import Detection, DetectionResult, ProcessingSettings, RuntimeStatus
from services.defect_history import DefectHistory
from services.frame_processor import FrameProcessor


class SuccessfulDetectionService:
    def detect(self, frame, settings):
        annotated = frame.copy()
        annotated[:, :] = 255
        return DetectionResult(
            annotated_frame=annotated,
            detections=[Detection("defect", 0.88, (1, 2, 3, 4))],
        )


class FailingDetectionService:
    def detect(self, frame, settings):
        return DetectionResult(
            annotated_frame=frame,
            detections=[],
            error="inference failed",
        )


def test_process_success_returns_frame_result_and_updates_history():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    processor = FrameProcessor(SuccessfulDetectionService(), history)

    result = processor.process(frame, ProcessingSettings())

    assert result.status == RuntimeStatus.READY
    assert result.source_frame is frame
    assert result.display_frame.mean() == 255
    assert len(result.detections) == 1
    assert result.stats.total == 1
    assert history.stats().total == 1
    assert result.processing_ms >= 0


def test_process_failure_returns_error_result_without_history_increment():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    processor = FrameProcessor(FailingDetectionService(), history)

    result = processor.process(frame, ProcessingSettings())

    assert result.status == RuntimeStatus.ERROR
    assert result.error == "inference failed"
    assert result.stats.total == 0
    assert history.stats().total == 0
