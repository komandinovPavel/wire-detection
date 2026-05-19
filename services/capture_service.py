from __future__ import annotations

from collections.abc import Callable
from typing import Any

from capture.camera import CameraCapture
from capture.image import ImageCapture
from capture.screen import ScreenCapture
from domain import SourceType
from utils.camera_utils import is_camera_available


class CaptureService:
    """Owns frame source lifecycle and source switching."""

    def __init__(
        self,
        image_factory: Callable[[], Any] = ImageCapture,
        screen_factory: Callable[[], Any] = ScreenCapture,
        camera_factory: Callable[[int], Any] = CameraCapture,
        camera_probe: Callable[[int], bool] | None = None,
    ):
        self._image_factory = image_factory
        self._screen_factory = screen_factory
        self._camera_factory = camera_factory
        self._camera_probe = camera_probe or self._probe_camera
        self._current_source: Any | None = None
        self.source_type = SourceType.NONE

    @property
    def current_source(self) -> Any | None:
        return self._current_source

    def load_image(self, path: str) -> Any:
        self.stop()
        source = self._image_factory()
        if not source.load(path):
            raise RuntimeError(f"Could not load image: {path}")
        source.start()
        self._current_source = source
        self.source_type = SourceType.IMAGE
        return source.read_frame()

    def start_screen(self) -> Any:
        return self._start_live_source(self._screen_factory(), SourceType.SCREEN)

    def start_camera(self, camera_index: int) -> Any:
        return self._start_live_source(self._camera_factory(camera_index), SourceType.CAMERA)

    def available_cameras(self, max_index: int = 5) -> list[int]:
        detected = [index for index in range(max_index) if self._camera_probe(index)]
        return detected or [0]

    def read_frame(self) -> Any:
        if self._current_source is None:
            return None
        return self._current_source.read_frame()

    def stop(self) -> None:
        if self._current_source is not None:
            self._current_source.stop()
        self._current_source = None
        self.source_type = SourceType.NONE

    def _start_live_source(self, source: Any, source_type: SourceType) -> Any:
        self.stop()
        if not source.start():
            raise RuntimeError(f"Could not start {source_type.value} source")
        self._current_source = source
        self.source_type = source_type
        return source

    def _probe_camera(self, index: int) -> bool:
        return is_camera_available(index)
