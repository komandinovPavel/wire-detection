import numpy as np

from domain import Detection, DetectionResult, ProcessingSettings, RuntimeStatus
from services.defect_event_filter import DefectEventFilter
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


class StableDetectionService:
    def detect(self, frame, settings):
        return DetectionResult(
            annotated_frame=frame,
            detections=[Detection("scratch", 0.9, (0, 0, 10, 10), timestamp=10.0)],
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


def test_process_preserves_current_detections_but_counts_only_new_events():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    processor = FrameProcessor(StableDetectionService(), history, event_filter)

    first = processor.process(frame, ProcessingSettings())
    second = processor.process(frame, ProcessingSettings())

    assert len(first.detections) == 1
    assert len(first.new_detections) == 1
    assert len(second.detections) == 1
    assert second.new_detections == []
    assert second.stats.total == 1


def test_process_counts_every_detection_when_deduplication_is_disabled():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    processor = FrameProcessor(StableDetectionService(), history, event_filter)
    settings = ProcessingSettings(deduplicate_defects=False)

    first = processor.process(frame, settings)
    second = processor.process(frame, settings)

    assert len(first.new_detections) == 1
    assert len(second.new_detections) == 1
    assert second.stats.total == 2


def test_process_failure_returns_error_result_without_history_increment():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    processor = FrameProcessor(FailingDetectionService(), history)

    result = processor.process(frame, ProcessingSettings())

    assert result.status == RuntimeStatus.ERROR
    assert result.error == "inference failed"
    assert result.stats.total == 0
    assert history.stats().total == 0
