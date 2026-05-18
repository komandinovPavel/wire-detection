from __future__ import annotations

from typing import Any

from app.runtime import ProcessingRuntime
from app.state import AppState
from domain import FrameResult, ProcessingSettings, RuntimeSnapshot, RuntimeStatus


class AppController:
    """Thin UI-facing facade for application use cases."""

    def __init__(
        self,
        capture_service: Any,
        frame_processor: Any,
        runtime: ProcessingRuntime,
        state: AppState | None = None,
    ):
        self._capture_service = capture_service
        self._frame_processor = frame_processor
        self._runtime = runtime
        self._state = state or AppState()
        self._latest_frame: FrameResult | None = None

    def load_image(self, path: str) -> FrameResult:
        self.stop()
        try:
            frame = self._capture_service.load_image(path)
            self._state.source_type = self._capture_service.source_type
            result = self._frame_processor.process(frame, self._state.settings)
            self._latest_frame = result
            self._state.status = result.status
            self._state.message = result.message
            self._state.stats = result.stats
            self._state.last_error = result.error
            return result
        except Exception as exc:
            result = FrameResult.error(str(exc))
            self._latest_frame = result
            self._state.status = RuntimeStatus.ERROR
            self._state.message = str(exc)
            self._state.last_error = str(exc)
            return result

    def start_camera(self, camera_index: int) -> None:
        self.stop()
        self._capture_service.start_camera(camera_index)
        self._state.source_type = self._capture_service.source_type
        self._state.status = RuntimeStatus.RUNNING
        self._state.message = f"Camera {camera_index} active"
        self._runtime.start()

    def start_screen(self) -> None:
        self.stop()
        self._capture_service.start_screen()
        self._state.source_type = self._capture_service.source_type
        self._state.status = RuntimeStatus.RUNNING
        self._state.message = "Screen capture active"
        self._runtime.start()

    def stop(self) -> None:
        self._runtime.stop()
        self._capture_service.stop()
        self._state.source_type = self._capture_service.source_type
        self._state.status = RuntimeStatus.STOPPED
        self._state.message = "Stopped"

    def set_confidence(self, value: float) -> None:
        clamped = max(0.0, min(1.0, float(value)))
        self._state.settings = ProcessingSettings(
            confidence=clamped,
            imgsz=self._state.settings.imgsz,
        )

    def poll_latest_frame(self) -> FrameResult | None:
        runtime_frame = self._runtime.poll_latest()
        if runtime_frame is not None:
            self._latest_frame = runtime_frame
            return runtime_frame
        return self._latest_frame

    def get_defects_snapshot(self):
        return self._state.stats

    def get_status(self) -> RuntimeSnapshot:
        return self._state.snapshot()
