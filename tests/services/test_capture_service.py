import numpy as np

from domain import SourceType
from services.capture_service import CaptureService


class DummyImageSource:
    def __init__(self, should_load=True):
        self.should_load = should_load
        self.loaded_path = None
        self.running = False
        self.stopped = False
        self.frame = np.zeros((2, 2, 3), dtype=np.uint8)

    def load(self, path):
        self.loaded_path = path
        return self.should_load

    def start(self):
        self.running = True
        return True

    def stop(self):
        self.stopped = True
        self.running = False

    def read_frame(self):
        return self.frame


class DummyLiveSource:
    def __init__(self, starts=True):
        self.starts = starts
        self.running = False
        self.stopped = False

    def start(self):
        self.running = self.starts
        return self.starts

    def stop(self):
        self.stopped = True
        self.running = False

    def read_frame(self):
        return np.ones((2, 2, 3), dtype=np.uint8)


def test_load_image_sets_current_source_and_returns_frame():
    image_source = DummyImageSource()
    service = CaptureService(image_factory=lambda: image_source)

    frame = service.load_image("sample.jpg")

    assert image_source.loaded_path == "sample.jpg"
    assert service.source_type is SourceType.IMAGE
    assert frame.shape == (2, 2, 3)


def test_switching_source_stops_previous_source():
    image_source = DummyImageSource()
    screen_source = DummyLiveSource()
    service = CaptureService(
        image_factory=lambda: image_source,
        screen_factory=lambda: screen_source,
    )

    service.load_image("sample.jpg")
    service.start_screen()

    assert image_source.stopped is True
    assert service.source_type is SourceType.SCREEN


def test_start_camera_uses_camera_index():
    created_indexes = []

    def camera_factory(index):
        created_indexes.append(index)
        return DummyLiveSource()

    service = CaptureService(camera_factory=camera_factory)

    service.start_camera(2)

    assert created_indexes == [2]
    assert service.source_type is SourceType.CAMERA


def test_load_image_raises_clear_error_when_file_cannot_load():
    service = CaptureService(image_factory=lambda: DummyImageSource(should_load=False))

    try:
        service.load_image("missing.jpg")
    except RuntimeError as exc:
        assert "Could not load image" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
