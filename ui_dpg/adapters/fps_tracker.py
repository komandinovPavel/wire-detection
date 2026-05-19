from __future__ import annotations

import math
from dataclasses import dataclass

from domain import SourceType
from ui_dpg.adapters.status_metrics import LIVE_SOURCES


@dataclass(frozen=True)
class FpsSample:
    timestamp: float
    fps: float


class FpsTracker:
    def __init__(self, window_seconds: float = 5.0) -> None:
        self._window_seconds = float(window_seconds)
        self._last_frame_key = None
        self._last_timestamp: float | None = None
        self._current_fps: float | None = None
        self._samples: list[FpsSample] = []

    @property
    def current_fps(self) -> float | None:
        return self._current_fps

    @property
    def samples(self) -> tuple[FpsSample, ...]:
        return tuple(self._samples)

    def observe(self, source_type: SourceType, frame_key, now: float) -> float | None:
        if source_type not in LIVE_SOURCES:
            self.clear()
            return None
        if frame_key is None or frame_key is self._last_frame_key:
            return self._current_fps

        fps = self._fps_from_interval(now)
        self._last_frame_key = frame_key
        self._last_timestamp = now
        if fps is not None:
            self._current_fps = fps
            self._samples.append(FpsSample(timestamp=now, fps=fps))
            self._prune(now)
        return self._current_fps

    def clear(self) -> None:
        self._last_frame_key = None
        self._last_timestamp = None
        self._current_fps = None
        self._samples.clear()

    def _fps_from_interval(self, now: float) -> float | None:
        if self._last_timestamp is None:
            return None
        interval = now - self._last_timestamp
        if interval <= 0 or not math.isfinite(interval):
            return None
        return 1.0 / interval

    def _prune(self, now: float) -> None:
        cutoff = now - self._window_seconds
        self._samples = [sample for sample in self._samples if sample.timestamp >= cutoff]
