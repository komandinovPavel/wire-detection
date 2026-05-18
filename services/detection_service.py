from __future__ import annotations

from typing import Any

from domain import Detection, DetectionResult, ProcessingSettings


class DetectionService:
    """Typed adapter around a detector with a predict(frame, conf, imgsz) method."""

    def __init__(self, detector: Any):
        self._detector = detector

    def detect(self, frame: Any, settings: ProcessingSettings) -> DetectionResult:
        try:
            annotated_frame, raw_detections = self._detector.predict(
                frame,
                conf=settings.confidence,
                imgsz=settings.imgsz,
            )
            detections = [self._to_detection(item) for item in raw_detections]
            return DetectionResult(
                annotated_frame=annotated_frame,
                detections=detections,
            )
        except Exception as exc:
            return DetectionResult(
                annotated_frame=frame,
                detections=[],
                error=str(exc),
            )

    def _to_detection(self, item: dict[str, Any]) -> Detection:
        return Detection(
            class_name=str(item.get("class", "Unknown")),
            confidence=float(item.get("confidence", 0.0)),
            bbox=item.get("bbox", (0.0, 0.0, 0.0, 0.0)),
        )
