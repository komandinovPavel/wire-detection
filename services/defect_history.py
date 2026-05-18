from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from domain import DefectStats, Detection


class DefectHistory:
    """Bounded recent detection history with cumulative statistics."""

    def __init__(self, max_items: int = 100):
        if max_items <= 0:
            raise ValueError("max_items must be positive")
        self._items: deque[Detection] = deque(maxlen=max_items)
        self._class_counts: Counter[str] = Counter()
        self._total = 0

    def add(self, detections: Iterable[Detection]) -> None:
        for detection in detections:
            self._items.appendleft(detection)
            self._class_counts[detection.class_name] += 1
            self._total += 1

    def recent(self) -> list[Detection]:
        return list(self._items)

    def stats(self) -> DefectStats:
        return DefectStats(total=self._total, by_class=dict(self._class_counts))

    def clear(self) -> None:
        self._items.clear()
        self._class_counts.clear()
        self._total = 0
