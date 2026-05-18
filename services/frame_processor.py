from __future__ import annotations

from time import perf_counter
from typing import Any

from domain import FrameResult, ProcessingSettings, RuntimeStatus
from services.defect_event_filter import DefectEventFilter
from services.defect_history import DefectHistory
from services.detection_service import DetectionService


class FrameProcessor:
    """Use case for processing exactly one source frame."""

    def __init__(
        self,
        detection_service: DetectionService,
        history: DefectHistory,
        event_filter: DefectEventFilter | None = None,
    ):
        self._detection_service = detection_service
        self._history = history
        self._event_filter = event_filter or DefectEventFilter()

    def clear_history(self) -> None:
        self._history.clear()
        self._event_filter.clear()

    def stats(self):
        return self._history.stats()

    def process(self, frame: Any, settings: ProcessingSettings) -> FrameResult:
        started = perf_counter()
        detection_result = self._detection_service.detect(frame, settings)
        elapsed_ms = (perf_counter() - started) * 1000.0

        if detection_result.error:
            return FrameResult(
                source_frame=frame,
                display_frame=detection_result.annotated_frame,
                detections=[],
                stats=self._history.stats(),
                status=RuntimeStatus.ERROR,
                message=detection_result.error,
                error=detection_result.error,
                processing_ms=elapsed_ms,
            )

        if settings.deduplicate_defects:
            new_detections = self._event_filter.filter_new(detection_result.detections)
        else:
            new_detections = detection_result.detections
        self._history.add(new_detections)
        return FrameResult(
            source_frame=frame,
            display_frame=detection_result.annotated_frame,
            detections=detection_result.detections,
            new_detections=new_detections,
            stats=self._history.stats(),
            status=RuntimeStatus.READY,
            message=f"Detections: {len(detection_result.detections)} | New: {len(new_detections)}",
            processing_ms=elapsed_ms,
        )
