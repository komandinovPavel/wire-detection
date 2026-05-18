from __future__ import annotations

from app.controller import AppController
from app.runtime import ProcessingRuntime
from app.state import AppState
from core.config import Config
from core.model import DefectDetector
from services import CaptureService, DefectHistory, DetectionService, FrameProcessor


def build_controller(config: Config | None = None) -> AppController:
    config = config or Config()
    state = AppState()
    detector = DefectDetector(config.MODEL_PATH)
    history = DefectHistory()
    capture_service = CaptureService()
    detection_service = DetectionService(detector)
    frame_processor = FrameProcessor(detection_service, history)
    runtime = ProcessingRuntime(capture_service, frame_processor, state)
    return AppController(capture_service, frame_processor, runtime, state)
