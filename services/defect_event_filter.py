from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Sequence

from domain import Detection


def bbox_iou(left: Sequence[float], right: Sequence[float]) -> float:
    left_x1, left_y1, left_x2, left_y2 = left
    right_x1, right_y1, right_x2, right_y2 = right

    inter_x1 = max(left_x1, right_x1)
    inter_y1 = max(left_y1, right_y1)
    inter_x2 = min(left_x2, right_x2)
    inter_y2 = min(left_y2, right_y2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h

    left_area = max(0.0, left_x2 - left_x1) * max(0.0, left_y2 - left_y1)
    right_area = max(0.0, right_x2 - right_x1) * max(0.0, right_y2 - right_y1)
    union = left_area + right_area - intersection
    if union <= 0:
        return 0.0
    return intersection / union


@dataclass
class _TrackedEvent:
    detection: Detection
    last_seen: float


class DefectEventFilter:
    """Converts per-frame detections into deduplicated defect events."""

    def __init__(self, iou_threshold: float = 0.4, window_seconds: float = 2.0):
        self._iou_threshold = iou_threshold
        self._window_seconds = window_seconds
        self._events: list[_TrackedEvent] = []

    def filter_new(self, detections: list[Detection], now: float | None = None) -> list[Detection]:
        now = perf_counter() if now is None else now
        self._events = [
            event for event in self._events
            if now - event.last_seen <= self._window_seconds
        ]

        new_events: list[Detection] = []
        for detection in detections:
            match = self._find_match(detection, now)
            if match is None:
                self._events.append(_TrackedEvent(detection=detection, last_seen=now))
                new_events.append(detection)
            else:
                match.detection = detection
                match.last_seen = now
        return new_events

    def clear(self) -> None:
        self._events.clear()

    def _find_match(self, detection: Detection, now: float) -> _TrackedEvent | None:
        for event in self._events:
            if now - event.last_seen > self._window_seconds:
                continue
            if event.detection.class_name != detection.class_name:
                continue
            if bbox_iou(event.detection.bbox, detection.bbox) >= self._iou_threshold:
                return event
        return None
