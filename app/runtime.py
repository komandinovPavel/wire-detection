from __future__ import annotations

import threading
import time
from typing import Any

from app.state import AppState
from domain import FrameResult, RuntimeStatus


class ProcessingRuntime:
    """Background runtime for live sources, with a testable single-iteration method."""

    def __init__(self, capture_service: Any, frame_processor: Any, state: AppState, interval_s: float = 0.01):
        self._capture_service = capture_service
        self._frame_processor = frame_processor
        self._state = state
        self._interval_s = interval_s
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._latest: FrameResult | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        self.stop(join=False)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, join: bool = True) -> None:
        self._stop_event.set()
        if join and self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def run_once(self) -> bool:
        frame = self._capture_service.read_frame()
        if frame is None:
            return False

        result = self._frame_processor.process(frame, self._state.settings)
        self._store_result(result)
        return True

    def poll_latest(self) -> FrameResult | None:
        with self._lock:
            return self._latest

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self.run_once()
            time.sleep(self._interval_s)

    def _store_result(self, result: FrameResult) -> None:
        with self._lock:
            self._latest = result
        self._state.stats = result.stats
        self._state.message = result.message
        self._state.status = result.status if result.status is RuntimeStatus.ERROR else RuntimeStatus.RUNNING
        self._state.last_error = result.error
