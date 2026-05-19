from app.controller import AppController
from app.state import AppState
from domain import (
    AppMode,
    CalibrationResult,
    DefectStats,
    FrameResult,
    MeasurementResult,
    ProcessingSettings,
    RuntimeStatus,
    SourceType,
)


class StubCaptureService:
    def __init__(self):
        self.source_type = SourceType.NONE
        self.stopped = False
        self.camera_index = None
        self.screen_started = False
        self.frame = object()
        self.available = [0]
        self.raise_on_camera = False

    def load_image(self, path):
        self.source_type = SourceType.IMAGE
        return self.frame

    def start_camera(self, index):
        if self.raise_on_camera:
            raise RuntimeError(f"Camera {index} failed")
        self.camera_index = index
        self.source_type = SourceType.CAMERA

    def start_screen(self):
        self.screen_started = True
        self.source_type = SourceType.SCREEN

    def stop(self):
        self.stopped = True
        self.source_type = SourceType.NONE

    def available_cameras(self, max_index=5):
        return self.available


class StubRuntime:
    def __init__(self):
        self.is_running = False
        self.latest = None
        self.stopped = False

    def start(self):
        self.is_running = True

    def stop(self):
        self.stopped = True
        self.is_running = False

    def clear_latest(self):
        self.latest = None

    def poll_latest(self):
        return self.latest


class StubProcessor:
    def __init__(self):
        self.cleared = False

    def process(self, frame, settings):
        return FrameResult(
            source_frame=frame,
            display_frame=frame,
            status=RuntimeStatus.READY,
            message=f"conf={settings.confidence}",
            stats=DefectStats(total=0, by_class={}),
        )

    def clear_history(self):
        self.cleared = True

    def stats(self):
        return DefectStats(total=0, by_class={})


class StubCalibrationService:
    def __init__(self):
        self.pixels_per_mm = None
        self.calibrated_at = []
        self.measured_at = []
        self.reset_called = False

    def is_calibrated(self):
        return self.pixels_per_mm is not None

    def calibrate_at(self, frame, x):
        self.calibrated_at.append((frame, x))
        self.pixels_per_mm = 100.0
        return CalibrationResult(
            x=x,
            calibration_diameter_px=188.0,
            measured_diameter_px=190.0,
            measured_diameter_mm=1.9,
            pixels_per_mm=100.0,
            top_y=10,
            bottom_y=198,
            slope=0.0,
            nominal_diameter_mm=1.88,
            tolerance_ok=0.03,
            tolerance_warn=0.07,
        )

    def measure_at(self, frame, x):
        self.measured_at.append((frame, x))
        return MeasurementResult(
            x=x,
            diameter_px=188.0,
            diameter_mm=1.88,
            pixels_per_mm=100.0,
            top_y=10,
            bottom_y=198,
            slope=0.0,
            nominal_diameter_mm=1.88,
            tolerance_ok=0.03,
            tolerance_warn=0.07,
        )

    def reset(self):
        self.reset_called = True
        self.pixels_per_mm = None


class StubMeasurementOverlay:
    def render_calibration(self, frame, result):
        return ("calibration_overlay", frame, result)

    def render_measurement(self, frame, result):
        return ("measurement_overlay", frame, result)


def make_controller():
    state = AppState()
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    calibration = StubCalibrationService()
    overlay = StubMeasurementOverlay()
    controller = AppController(capture, processor, runtime, state, calibration, overlay)
    return controller, capture, runtime


def test_set_confidence_updates_state():
    controller, _, _ = make_controller()

    controller.set_confidence(0.65)

    assert controller.get_status().settings.confidence == 0.65


def test_set_confidence_clamps_below_zero():
    controller, _, _ = make_controller()

    controller.set_confidence(-0.25)

    assert controller.get_status().settings.confidence == 0.0


def test_set_confidence_clamps_above_one():
    controller, _, _ = make_controller()

    controller.set_confidence(1.25)

    assert controller.get_status().settings.confidence == 1.0


def test_set_confidence_preserves_current_imgsz():
    state = AppState(settings=ProcessingSettings(confidence=0.3, imgsz=320))
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    controller = AppController(capture, processor, runtime, state)

    controller.set_confidence(0.8)

    assert controller.get_status().settings.imgsz == 320


def test_set_confidence_preserves_deduplication_setting():
    state = AppState(settings=ProcessingSettings(confidence=0.3, imgsz=320, deduplicate_defects=False))
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    controller = AppController(capture, processor, runtime, state)

    controller.set_confidence(0.8)

    assert controller.get_status().settings.deduplicate_defects is False


def test_set_deduplication_enabled_updates_state_and_preserves_other_settings():
    state = AppState(settings=ProcessingSettings(confidence=0.42, imgsz=320))
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    controller = AppController(capture, processor, runtime, state)

    controller.set_deduplication_enabled(False)

    assert controller.get_status().settings.deduplicate_defects is False
    assert controller.get_status().settings.confidence == 0.42
    assert controller.get_status().settings.imgsz == 320


def test_set_yolo_enabled_updates_state_and_preserves_other_settings():
    state = AppState(settings=ProcessingSettings(confidence=0.42, imgsz=320, deduplicate_defects=False))
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    controller = AppController(capture, processor, runtime, state)

    controller.set_yolo_enabled(False)

    assert controller.get_status().settings.yolo_enabled is False
    assert controller.get_status().settings.deduplicate_defects is False
    assert controller.get_status().settings.confidence == 0.42
    assert controller.get_status().settings.imgsz == 320


def test_load_image_processes_single_frame_and_updates_snapshot():
    controller, capture, _ = make_controller()

    result = controller.load_image("image.jpg")

    assert capture.source_type is SourceType.IMAGE
    assert result.message == "conf=0.3"
    assert controller.poll_latest_frame() is result
    assert controller.get_status().source_type is SourceType.IMAGE


def test_load_image_stops_streaming_sources_and_discards_stale_runtime_frame():
    controller, capture, runtime = make_controller()
    stale = FrameResult(source_frame=object(), display_frame=object(), message="stale")
    runtime.latest = stale
    controller.start_screen()
    runtime.latest = stale

    result = controller.load_image("image.jpg")

    assert runtime.stopped is True
    assert capture.stopped is True
    assert runtime.latest is None
    assert controller.poll_latest_frame() is result
    assert controller.get_status().source_type is SourceType.IMAGE


def test_start_camera_delegates_to_runtime():
    controller, capture, runtime = make_controller()

    controller.start_camera(1)

    assert capture.camera_index == 1
    assert runtime.is_running is True
    assert controller.get_status().status is RuntimeStatus.RUNNING


def test_list_cameras_delegates_to_capture_service():
    controller, capture, _ = make_controller()
    capture.available = [0, 2]

    assert controller.list_cameras() == [0, 2]


def test_clear_defects_resets_processor_history_and_state_stats():
    state = AppState(stats=DefectStats(total=5, by_class={"scratch": 5}))
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    controller = AppController(capture, processor, runtime, state)

    controller.clear_defects()

    assert processor.cleared is True
    assert controller.get_status().stats.total == 0


def test_start_camera_failure_sets_error_status_without_starting_runtime():
    controller, capture, runtime = make_controller()
    capture.raise_on_camera = True

    controller.start_camera(3)

    assert runtime.is_running is False
    assert controller.get_status().status is RuntimeStatus.ERROR
    assert "Camera" in controller.get_status().message


def test_load_calibration_image_loads_frame_without_running_detection():
    controller, capture, runtime = make_controller()

    frame = controller.load_calibration_image("calibration.jpg")

    assert frame is capture.frame
    assert runtime.is_running is False
    assert controller.get_status().mode is AppMode.CALIBRATE


def test_calibrate_at_uses_loaded_calibration_frame_and_returns_overlay():
    controller, capture, _ = make_controller()
    controller.load_calibration_image("calibration.jpg")

    result, overlay = controller.calibrate_at(42)

    assert result.pixels_per_mm == 100.0
    assert overlay[0] == "calibration_overlay"
    assert overlay[1] is capture.frame
    assert controller.is_calibrated() is True


def test_start_measurement_mode_freezes_latest_source_frame():
    controller, capture, runtime = make_controller()
    controller.load_calibration_image("calibration.jpg")
    controller.calibrate_at(42)
    frame = object()
    runtime.latest = FrameResult(source_frame=object(), display_frame=object())
    controller._latest_frame = FrameResult(source_frame=frame, display_frame=object())

    frozen = controller.start_measurement_mode()

    assert frozen is frame
    assert runtime.latest is None
    assert capture.stopped is True
    assert controller.get_status().measurement_enabled is True
    assert controller.get_status().mode is AppMode.DETECT


def test_measurement_toggle_requires_calibration():
    controller, _, _ = make_controller()

    enabled = controller.set_measurement_enabled(True)

    assert enabled is False
    assert controller.get_status().measurement_enabled is False
    assert controller.get_status().status is RuntimeStatus.ERROR
    assert "Calibrate first" in controller.get_status().message


def test_measurement_toggle_can_be_enabled_after_calibration_and_survives_source_switch():
    controller, _, _ = make_controller()
    controller.load_calibration_image("calibration.jpg")
    controller.calibrate_at(42)

    enabled = controller.set_measurement_enabled(True)
    controller.start_screen()

    assert enabled is True
    assert controller.get_status().measurement_enabled is True
    assert controller.get_status().mode is AppMode.DETECT
    assert controller.get_status().source_type is SourceType.SCREEN


def test_measurement_toggle_can_be_disabled():
    controller, _, _ = make_controller()
    controller.load_calibration_image("calibration.jpg")
    controller.calibrate_at(42)
    controller.set_measurement_enabled(True)

    enabled = controller.set_measurement_enabled(False)

    assert enabled is False
    assert controller.get_status().measurement_enabled is False


def test_measure_at_uses_frozen_measurement_frame():
    controller, capture, _ = make_controller()
    controller.load_calibration_image("calibration.jpg")
    controller.calibrate_at(42)
    controller.start_measurement_mode()

    result, overlay = controller.measure_at(50)

    assert result.diameter_mm == 1.88
    assert overlay[0] == "measurement_overlay"
    assert overlay[1] is capture.frame


def test_clear_output_resets_latest_frame_and_stats():
    controller, _, _ = make_controller()
    controller._latest_frame = FrameResult(source_frame=object(), display_frame=object())

    controller.clear_output()

    assert controller.poll_latest_frame() is None
    assert controller.get_status().stats.total == 0


def test_stop_stops_runtime_and_capture():
    controller, capture, runtime = make_controller()
    controller.start_screen()

    controller.stop()

    assert runtime.is_running is False
    assert capture.stopped is True
    assert controller.get_status().status is RuntimeStatus.STOPPED
