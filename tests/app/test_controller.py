from app.controller import AppController
from app.state import AppState
from domain import DefectStats, FrameResult, ProcessingSettings, RuntimeStatus, SourceType


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


def make_controller():
    state = AppState()
    capture = StubCaptureService()
    processor = StubProcessor()
    runtime = StubRuntime()
    controller = AppController(capture, processor, runtime, state)
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


def test_load_image_processes_single_frame_and_updates_snapshot():
    controller, capture, _ = make_controller()

    result = controller.load_image("image.jpg")

    assert capture.source_type is SourceType.IMAGE
    assert result.message == "conf=0.3"
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


def test_stop_stops_runtime_and_capture():
    controller, capture, runtime = make_controller()
    controller.start_screen()

    controller.stop()

    assert runtime.is_running is False
    assert capture.stopped is True
    assert controller.get_status().status is RuntimeStatus.STOPPED
