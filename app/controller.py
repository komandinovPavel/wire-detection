from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.runtime import ProcessingRuntime
from app.state import AppState
from domain import AppMode, FrameResult, ProcessingSettings, RuntimeSnapshot, RuntimeStatus
from services.calibration_service import CalibrationService
from services.measurement_overlay import MeasurementOverlay


class AppController:
    """Thin UI-facing facade for application use cases."""

    def __init__(
        self,
        capture_service: Any,
        frame_processor: Any,
        runtime: ProcessingRuntime,
        state: AppState,
        calibration_service: Any | None = None,
        measurement_overlay: Any | None = None,
    ):
        self._capture_service = capture_service
        self._frame_processor = frame_processor
        self._runtime = runtime
        self._state = state
        self._calibration_service = calibration_service or CalibrationService()
        self._measurement_overlay = measurement_overlay or MeasurementOverlay()
        self._latest_frame: FrameResult | None = None
        self._calibration_frame: Any | None = None
        self._measurement_frame: Any | None = None

    def load_image(self, path: str) -> FrameResult:
        self.stop_streaming_sources()
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
        try:
            self._capture_service.start_camera(camera_index)
            self._state.source_type = self._capture_service.source_type
            self._state.status = RuntimeStatus.RUNNING
            self._state.message = f"Camera {camera_index} active"
            self._state.last_error = None
            self._runtime.start()
        except Exception as exc:
            self._state.source_type = self._capture_service.source_type
            self._state.status = RuntimeStatus.ERROR
            self._state.message = str(exc)
            self._state.last_error = str(exc)

    def start_screen(self) -> None:
        self.stop()
        try:
            self._capture_service.start_screen()
            self._state.source_type = self._capture_service.source_type
            self._state.status = RuntimeStatus.RUNNING
            self._state.message = "Screen capture active"
            self._state.last_error = None
            self._runtime.start()
        except Exception as exc:
            self._state.source_type = self._capture_service.source_type
            self._state.status = RuntimeStatus.ERROR
            self._state.message = str(exc)
            self._state.last_error = str(exc)

    def stop(self) -> None:
        self.stop_streaming_sources()
        self._state.source_type = self._capture_service.source_type
        self._state.status = RuntimeStatus.STOPPED
        self._state.message = "Stopped"

    def stop_streaming_sources(self) -> None:
        self._runtime.stop()
        self._runtime.clear_latest()
        self._capture_service.stop()
        self._state.source_type = self._capture_service.source_type

    def set_confidence(self, value: float) -> None:
        clamped = max(0.0, min(1.0, float(value)))
        self._state.settings = replace(self._state.settings, confidence=clamped)

    def set_deduplication_enabled(self, enabled: bool) -> None:
        self._state.settings = replace(self._state.settings, deduplicate_defects=bool(enabled))

    def set_yolo_enabled(self, enabled: bool) -> None:
        self._state.settings = replace(self._state.settings, yolo_enabled=bool(enabled))

    def list_cameras(self, max_index: int = 5) -> list[int]:
        return self._capture_service.available_cameras(max_index)

    def clear_defects(self) -> None:
        self._frame_processor.clear_history()
        self._state.stats = self._frame_processor.stats()

    def clear_output(self) -> None:
        self.clear_defects()
        self._latest_frame = None
        self._measurement_frame = None

    def load_calibration_image(self, path: str) -> Any:
        self.stop()
        frame = self._capture_service.load_image(path)
        self._calibration_frame = frame
        self._measurement_frame = frame
        self._state.source_type = self._capture_service.source_type
        self._state.mode = AppMode.CALIBRATE
        self._state.status = RuntimeStatus.READY
        self._state.message = "Calibration image loaded"
        self._state.last_error = None
        return frame

    def calibrate_at(self, x: int):
        if self._calibration_frame is None:
            raise RuntimeError("Calibration image is not loaded")
        result = self._calibration_service.calibrate_at(self._calibration_frame, x)
        overlay = self._measurement_overlay.render_calibration(self._calibration_frame, result)
        self._measurement_frame = self._calibration_frame
        self._state.mode = AppMode.DETECT
        self._state.status = RuntimeStatus.READY
        self._state.message = f"Calibrated: {result.pixels_per_mm:.3f} px/mm"
        self._state.last_error = None
        return result, overlay

    def is_calibrated(self) -> bool:
        return self._calibration_service.is_calibrated()

    def reset_calibration(self) -> None:
        self._calibration_service.reset()
        self._state.measurement_enabled = False
        self._state.mode = AppMode.DETECT
        self._state.message = "Calibration reset"

    def set_measurement_enabled(self, enabled: bool) -> bool:
        if not enabled:
            self._state.measurement_enabled = False
            self._state.mode = AppMode.DETECT
            self._state.status = RuntimeStatus.READY
            self._state.message = "Measurement mode disabled"
            self._state.last_error = None
            return False
        if not self._calibration_service.is_calibrated():
            self._state.measurement_enabled = False
            self._state.status = RuntimeStatus.ERROR
            self._state.message = "Calibrate first"
            self._state.last_error = "Calibrate first"
            return False
        self._state.measurement_enabled = True
        self._state.mode = AppMode.DETECT
        self._state.status = RuntimeStatus.READY
        self._state.message = "Measure mode enabled: click on the wire"
        self._state.last_error = None
        return True

    def start_measurement_mode(self) -> Any:
        if not self._calibration_service.is_calibrated():
            self._state.status = RuntimeStatus.ERROR
            self._state.message = "Calibrate first"
            self._state.last_error = "Calibrate first"
            raise RuntimeError("Calibrate first")
        if self._latest_frame is not None and self._latest_frame.source_frame is not None:
            self._measurement_frame = self._latest_frame.source_frame
        elif self._measurement_frame is None:
            self._state.status = RuntimeStatus.ERROR
            self._state.message = "No frame available for measurement"
            self._state.last_error = "No frame available for measurement"
            raise RuntimeError("No frame available for measurement")
        self.stop_streaming_sources()
        self._state.measurement_enabled = True
        self._state.mode = AppMode.DETECT
        self._state.status = RuntimeStatus.READY
        self._state.message = "Measurement mode: click on the wire"
        return self._measurement_frame

    def measure_at(self, x: int):
        if self._measurement_frame is None:
            raise RuntimeError("No frame available for measurement")
        result = self._calibration_service.measure_at(self._measurement_frame, x)
        overlay = self._measurement_overlay.render_measurement(self._measurement_frame, result)
        self._state.mode = AppMode.DETECT
        self._state.status = RuntimeStatus.READY
        self._state.message = f"Measured: {result.diameter_mm:.3f} mm | Deviation: {result.deviation_mm:+.3f} mm"
        self._state.last_error = None
        return result, overlay

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
