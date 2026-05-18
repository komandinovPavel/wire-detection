from __future__ import annotations

from app.controller import AppController
from app.runtime import ProcessingRuntime
from app.state import AppState
from core.config import Config
from core.model import DefectDetector
from services import (
    CalibrationService,
    CaptureService,
    DefectHistory,
    DetectionService,
    FrameProcessor,
    MeasurementOverlay,
)


def build_controller(config: Config | None = None) -> AppController:
    config = config or Config()
    state = AppState()
    detector = DefectDetector(config.MODEL_PATH)
    history = DefectHistory()
    capture_service = CaptureService()
    detection_service = DetectionService(detector)
    frame_processor = FrameProcessor(detection_service, history)
    calibration_service = CalibrationService(
        nominal_diameter_mm=getattr(config, "NOMINAL_DIAMETER_MM", Config.NOMINAL_DIAMETER_MM),
        tolerance_ok=getattr(config, "TOLERANCE_OK", Config.TOLERANCE_OK),
        tolerance_warn=getattr(config, "TOLERANCE_WARN", Config.TOLERANCE_WARN),
    )
    measurement_overlay = MeasurementOverlay()
    runtime = ProcessingRuntime(capture_service, frame_processor, state)
    return AppController(
        capture_service,
        frame_processor,
        runtime,
        state,
        calibration_service,
        measurement_overlay,
    )
