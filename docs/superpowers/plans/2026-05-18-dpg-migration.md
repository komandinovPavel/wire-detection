# Dear PyGui Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean backend/service layer and a first Dear PyGui MVP for image, screen, and camera defect detection.

**Architecture:** The implementation separates UI from backend through a thin `AppController`. Domain dataclasses define contracts, services process frames and manage sources, and Dear PyGui only renders state and sends commands.

**Tech Stack:** Python, NumPy, OpenCV, Ultralytics YOLO, Dear PyGui, pytest.

---

## Scope Check

This plan implements the first DPG MVP from `docs/superpowers/specs/2026-05-18-dpg-migration-design.md`: image/screen/camera sources, YOLO detection, confidence control, defect history, statistics, status, and a DPG viewport. Calibration and measurement are intentionally outside this first implementation plan.

## File Map

- Create `domain/__init__.py`: exports domain contracts.
- Create `domain/enums.py`: `SourceType`, `AppMode`, `RuntimeStatus`.
- Create `domain/models.py`: `Detection`, `DetectionResult`, `FrameResult`, `ProcessingSettings`, `DefectStats`, `RuntimeSnapshot`.
- Create `services/__init__.py`: exports service classes.
- Create `services/defect_history.py`: bounded detection history and stats.
- Create `services/detection_service.py`: typed adapter around `core.model.DefectDetector`.
- Create `services/frame_processor.py`: process one frame with settings and history.
- Create `services/capture_service.py`: image/screen/camera source lifecycle.
- Create `services/overlay_service.py`: small pass-through overlay service that gives later calibration and measurement overlays a clear home.
- Create `app/__init__.py`: exports application classes.
- Create `app/state.py`: mutable app state holder.
- Create `app/runtime.py`: background capture processing loop.
- Create `app/controller.py`: thin command facade for UI.
- Create `ui_dpg/__init__.py`: package marker.
- Create `ui_dpg/adapters/frame_texture.py`: frame resizing and DPG texture conversion helpers.
- Create `ui_dpg/views/control_panel.py`: DPG control widgets.
- Create `ui_dpg/views/viewport.py`: DPG image viewport.
- Create `ui_dpg/views/defects_panel.py`: DPG defect table and stats.
- Create `ui_dpg/views/status_bar.py`: DPG status text.
- Create `ui_dpg/app.py`: DPG application assembly and render loop.
- Create `main_dpg.py`: DPG entry point.
- Create tests under `tests/domain`, `tests/services`, and `tests/app`.
- Modify `docs/modules/*.md` if implementation names differ from current module docs.
- Modify `architecrute.md` after code lands to mention the new DPG path.

---

### Task 1: Domain Contracts

**Files:**
- Create: `domain/__init__.py`
- Create: `domain/enums.py`
- Create: `domain/models.py`
- Test: `tests/domain/test_models.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/domain/test_models.py`:

```python
from domain import (
    AppMode,
    DefectStats,
    Detection,
    FrameResult,
    ProcessingSettings,
    RuntimeSnapshot,
    RuntimeStatus,
    SourceType,
)


def test_processing_settings_defaults_match_existing_config_values():
    settings = ProcessingSettings()

    assert settings.confidence == 0.3
    assert settings.imgsz == 640


def test_detection_bbox_is_normalized_to_tuple():
    detection = Detection(class_name="defect", confidence=0.8, bbox=[1, 2, 3, 4])

    assert detection.bbox == (1.0, 2.0, 3.0, 4.0)


def test_frame_result_error_factory_sets_error_status():
    result = FrameResult.error("camera failed")

    assert result.status == RuntimeStatus.ERROR
    assert result.error == "camera failed"
    assert result.detections == []


def test_runtime_snapshot_exposes_status_and_source():
    snapshot = RuntimeSnapshot(
        status=RuntimeStatus.RUNNING,
        source_type=SourceType.CAMERA,
        mode=AppMode.DETECT,
        message="Camera active",
        settings=ProcessingSettings(confidence=0.45),
        stats=DefectStats(total=2, by_class={"defect": 2}),
    )

    assert snapshot.status is RuntimeStatus.RUNNING
    assert snapshot.source_type is SourceType.CAMERA
    assert snapshot.settings.confidence == 0.45
    assert snapshot.stats.by_class["defect"] == 2
```

- [ ] **Step 2: Run the domain tests and verify they fail**

Run:

```bash
pytest tests/domain/test_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'domain'`.

- [ ] **Step 3: Implement domain enums**

Create `domain/enums.py`:

```python
from enum import Enum


class SourceType(str, Enum):
    NONE = "none"
    IMAGE = "image"
    SCREEN = "screen"
    CAMERA = "camera"


class AppMode(str, Enum):
    DETECT = "detect"
    CALIBRATE = "calibrate"
    MEASURE = "measure"


class RuntimeStatus(str, Enum):
    IDLE = "idle"
    LOADING_MODEL = "loading_model"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
```

- [ ] **Step 4: Implement domain models**

Create `domain/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Mapping, Sequence

from .enums import AppMode, RuntimeStatus, SourceType


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox: Sequence[float]
    timestamp: float = field(default_factory=perf_counter)

    def __post_init__(self) -> None:
        if len(self.bbox) != 4:
            raise ValueError("Detection bbox must contain exactly 4 values")
        normalized = tuple(float(value) for value in self.bbox)
        object.__setattr__(self, "bbox", normalized)


@dataclass(frozen=True)
class DetectionResult:
    annotated_frame: Any
    detections: list[Detection]
    error: str | None = None


@dataclass(frozen=True)
class ProcessingSettings:
    confidence: float = 0.3
    imgsz: int = 640


@dataclass(frozen=True)
class DefectStats:
    total: int = 0
    by_class: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameResult:
    source_frame: Any = None
    display_frame: Any = None
    detections: list[Detection] = field(default_factory=list)
    stats: DefectStats = field(default_factory=DefectStats)
    status: RuntimeStatus = RuntimeStatus.READY
    message: str = ""
    error: str | None = None
    processing_ms: float = 0.0

    @classmethod
    def error(cls, message: str, source_frame: Any = None) -> "FrameResult":
        return cls(
            source_frame=source_frame,
            display_frame=source_frame,
            status=RuntimeStatus.ERROR,
            message=message,
            error=message,
        )


@dataclass(frozen=True)
class RuntimeSnapshot:
    status: RuntimeStatus
    source_type: SourceType
    mode: AppMode
    message: str
    settings: ProcessingSettings
    stats: DefectStats
    last_error: str | None = None
```

- [ ] **Step 5: Export domain contracts**

Create `domain/__init__.py`:

```python
from .enums import AppMode, RuntimeStatus, SourceType
from .models import (
    DefectStats,
    Detection,
    DetectionResult,
    FrameResult,
    ProcessingSettings,
    RuntimeSnapshot,
)

__all__ = [
    "AppMode",
    "DefectStats",
    "Detection",
    "DetectionResult",
    "FrameResult",
    "ProcessingSettings",
    "RuntimeSnapshot",
    "RuntimeStatus",
    "SourceType",
]
```

- [ ] **Step 6: Run tests**

Run:

```bash
pytest tests/domain/test_models.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add domain tests/domain/test_models.py
git commit -m "feat: add domain contracts"
```

---

### Task 2: Defect History Service

**Files:**
- Create: `services/__init__.py`
- Create: `services/defect_history.py`
- Test: `tests/services/test_defect_history.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_defect_history.py`:

```python
from domain import Detection
from services.defect_history import DefectHistory


def make_detection(name: str = "defect", confidence: float = 0.75) -> Detection:
    return Detection(class_name=name, confidence=confidence, bbox=(1, 2, 3, 4))


def test_add_updates_total_and_class_counts():
    history = DefectHistory(max_items=10)

    history.add([make_detection("scratch"), make_detection("scratch"), make_detection("crack")])

    stats = history.stats()
    assert stats.total == 3
    assert stats.by_class == {"scratch": 2, "crack": 1}


def test_recent_is_limited_to_max_items_but_total_keeps_growing():
    history = DefectHistory(max_items=2)

    history.add([make_detection("a")])
    history.add([make_detection("b")])
    history.add([make_detection("c")])

    recent = history.recent()
    assert [item.class_name for item in recent] == ["c", "b"]
    assert history.stats().total == 3


def test_clear_resets_history_and_stats():
    history = DefectHistory(max_items=10)
    history.add([make_detection("defect")])

    history.clear()

    assert history.recent() == []
    assert history.stats().total == 0
    assert history.stats().by_class == {}
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
pytest tests/services/test_defect_history.py -v
```

Expected: FAIL with `ModuleNotFoundError` or import error for `services.defect_history`.

- [ ] **Step 3: Implement `DefectHistory`**

Create `services/defect_history.py`:

```python
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from domain import DefectStats, Detection


class DefectHistory:
    """Bounded recent detection history with cumulative statistics."""

    def __init__(self, max_items: int = 100):
        if max_items <= 0:
            raise ValueError("max_items must be positive")
        self._items: deque[Detection] = deque(maxlen=max_items)
        self._class_counts: Counter[str] = Counter()
        self._total = 0

    def add(self, detections: Iterable[Detection]) -> None:
        for detection in detections:
            self._items.appendleft(detection)
            self._class_counts[detection.class_name] += 1
            self._total += 1

    def recent(self) -> list[Detection]:
        return list(self._items)

    def stats(self) -> DefectStats:
        return DefectStats(total=self._total, by_class=dict(self._class_counts))

    def clear(self) -> None:
        self._items.clear()
        self._class_counts.clear()
        self._total = 0
```

- [ ] **Step 4: Export services**

Create `services/__init__.py`:

```python
from .defect_history import DefectHistory

__all__ = ["DefectHistory"]
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest tests/services/test_defect_history.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add services tests/services/test_defect_history.py
git commit -m "feat: add defect history service"
```

---

### Task 3: Detection Service and Frame Processor

**Files:**
- Create: `services/detection_service.py`
- Create: `services/frame_processor.py`
- Modify: `services/__init__.py`
- Test: `tests/services/test_detection_service.py`
- Test: `tests/services/test_frame_processor.py`

- [ ] **Step 1: Write detection service tests**

Create `tests/services/test_detection_service.py`:

```python
import numpy as np

from domain import Detection, ProcessingSettings, RuntimeStatus
from services.detection_service import DetectionService


class StubDetector:
    def __init__(self):
        self.calls = []

    def predict(self, frame, conf=0.3, imgsz=640):
        self.calls.append((frame, conf, imgsz))
        annotated = frame.copy()
        return annotated, [
            {"class": "defect", "confidence": 0.91, "bbox": [1, 2, 3, 4]},
        ]


class RaisingDetector:
    def predict(self, frame, conf=0.3, imgsz=640):
        raise RuntimeError("model exploded")


def test_detect_normalizes_detector_dicts_to_detections():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    detector = StubDetector()
    service = DetectionService(detector)

    result = service.detect(frame, ProcessingSettings(confidence=0.55, imgsz=320))

    assert detector.calls[0][1:] == (0.55, 320)
    assert isinstance(result.detections[0], Detection)
    assert result.detections[0].class_name == "defect"
    assert result.detections[0].confidence == 0.91
    assert result.error is None


def test_detect_returns_error_result_when_detector_raises():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    service = DetectionService(RaisingDetector())

    result = service.detect(frame, ProcessingSettings())

    assert result.annotated_frame is frame
    assert result.detections == []
    assert "model exploded" in result.error
```

- [ ] **Step 2: Write frame processor tests**

Create `tests/services/test_frame_processor.py`:

```python
import numpy as np

from domain import Detection, DetectionResult, ProcessingSettings, RuntimeStatus
from services.defect_history import DefectHistory
from services.frame_processor import FrameProcessor


class SuccessfulDetectionService:
    def detect(self, frame, settings):
        annotated = frame.copy()
        annotated[:, :] = 255
        return DetectionResult(
            annotated_frame=annotated,
            detections=[Detection("defect", 0.88, (1, 2, 3, 4))],
        )


class FailingDetectionService:
    def detect(self, frame, settings):
        return DetectionResult(
            annotated_frame=frame,
            detections=[],
            error="inference failed",
        )


def test_process_success_returns_frame_result_and_updates_history():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    processor = FrameProcessor(SuccessfulDetectionService(), history)

    result = processor.process(frame, ProcessingSettings())

    assert result.status == RuntimeStatus.READY
    assert result.source_frame is frame
    assert result.display_frame.mean() == 255
    assert len(result.detections) == 1
    assert result.stats.total == 1
    assert history.stats().total == 1
    assert result.processing_ms >= 0


def test_process_failure_returns_error_result_without_history_increment():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    processor = FrameProcessor(FailingDetectionService(), history)

    result = processor.process(frame, ProcessingSettings())

    assert result.status == RuntimeStatus.ERROR
    assert result.error == "inference failed"
    assert result.stats.total == 0
    assert history.stats().total == 0
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
pytest tests/services/test_detection_service.py tests/services/test_frame_processor.py -v
```

Expected: FAIL with import errors for `DetectionService` and `FrameProcessor`.

- [ ] **Step 4: Implement `DetectionService`**

Create `services/detection_service.py`:

```python
from __future__ import annotations

from typing import Any

from domain import Detection, DetectionResult, ProcessingSettings


class DetectionService:
    """Typed adapter around a detector with a predict(frame, conf, imgsz) method."""

    def __init__(self, detector: Any):
        self._detector = detector

    def detect(self, frame: Any, settings: ProcessingSettings) -> DetectionResult:
        try:
            annotated_frame, raw_detections = self._detector.predict(
                frame,
                conf=settings.confidence,
                imgsz=settings.imgsz,
            )
            detections = [self._to_detection(item) for item in raw_detections]
            return DetectionResult(
                annotated_frame=annotated_frame,
                detections=detections,
            )
        except Exception as exc:
            return DetectionResult(
                annotated_frame=frame,
                detections=[],
                error=str(exc),
            )

    def _to_detection(self, item: dict[str, Any]) -> Detection:
        return Detection(
            class_name=str(item.get("class", "Unknown")),
            confidence=float(item.get("confidence", 0.0)),
            bbox=item.get("bbox", (0.0, 0.0, 0.0, 0.0)),
        )
```

- [ ] **Step 5: Implement `FrameProcessor`**

Create `services/frame_processor.py`:

```python
from __future__ import annotations

from time import perf_counter
from typing import Any

from domain import FrameResult, ProcessingSettings, RuntimeStatus
from services.defect_history import DefectHistory
from services.detection_service import DetectionService


class FrameProcessor:
    """Use case for processing exactly one source frame."""

    def __init__(self, detection_service: DetectionService, history: DefectHistory):
        self._detection_service = detection_service
        self._history = history

    def process(self, frame: Any, settings: ProcessingSettings) -> FrameResult:
        started = perf_counter()
        detection_result = self._detection_service.detect(frame, settings)
        elapsed_ms = (perf_counter() - started) * 1000.0

        if detection_result.error:
            return FrameResult(
                source_frame=frame,
                display_frame=detection_result.annotated_frame,
                detections=[],
                stats=self._history.stats(),
                status=RuntimeStatus.ERROR,
                message=detection_result.error,
                error=detection_result.error,
                processing_ms=elapsed_ms,
            )

        self._history.add(detection_result.detections)
        return FrameResult(
            source_frame=frame,
            display_frame=detection_result.annotated_frame,
            detections=detection_result.detections,
            stats=self._history.stats(),
            status=RuntimeStatus.READY,
            message=f"Detections: {len(detection_result.detections)}",
            processing_ms=elapsed_ms,
        )
```

- [ ] **Step 6: Update service exports**

Replace `services/__init__.py` with:

```python
from .defect_history import DefectHistory
from .detection_service import DetectionService
from .frame_processor import FrameProcessor

__all__ = [
    "DefectHistory",
    "DetectionService",
    "FrameProcessor",
]
```

- [ ] **Step 7: Run tests**

Run:

```bash
pytest tests/services/test_detection_service.py tests/services/test_frame_processor.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add services tests/services/test_detection_service.py tests/services/test_frame_processor.py
git commit -m "feat: add detection frame processing services"
```

---

### Task 4: Capture Service

**Files:**
- Create: `services/capture_service.py`
- Modify: `services/__init__.py`
- Test: `tests/services/test_capture_service.py`

- [ ] **Step 1: Write capture service tests**

Create `tests/services/test_capture_service.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
pytest tests/services/test_capture_service.py -v
```

Expected: FAIL with import error for `CaptureService`.

- [ ] **Step 3: Implement `CaptureService`**

Create `services/capture_service.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from capture.camera import CameraCapture
from capture.image import ImageCapture
from capture.screen import ScreenCapture
from domain import SourceType


class CaptureService:
    """Owns frame source lifecycle and source switching."""

    def __init__(
        self,
        image_factory: Callable[[], Any] = ImageCapture,
        screen_factory: Callable[[], Any] = ScreenCapture,
        camera_factory: Callable[[int], Any] = CameraCapture,
    ):
        self._image_factory = image_factory
        self._screen_factory = screen_factory
        self._camera_factory = camera_factory
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
```

- [ ] **Step 4: Update service exports**

Replace `services/__init__.py` with:

```python
from .capture_service import CaptureService
from .defect_history import DefectHistory
from .detection_service import DetectionService
from .frame_processor import FrameProcessor

__all__ = [
    "CaptureService",
    "DefectHistory",
    "DetectionService",
    "FrameProcessor",
]
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest tests/services/test_capture_service.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add services/capture_service.py services/__init__.py tests/services/test_capture_service.py
git commit -m "feat: add capture service"
```

---

### Task 5: App State, Runtime, and Controller

**Files:**
- Create: `app/__init__.py`
- Create: `app/state.py`
- Create: `app/runtime.py`
- Create: `app/controller.py`
- Test: `tests/app/test_controller.py`
- Test: `tests/app/test_runtime.py`

- [ ] **Step 1: Write controller tests**

Create `tests/app/test_controller.py`:

```python
from app.controller import AppController
from app.state import AppState
from domain import DefectStats, FrameResult, RuntimeStatus, SourceType


class StubCaptureService:
    def __init__(self):
        self.source_type = SourceType.NONE
        self.stopped = False
        self.camera_index = None
        self.screen_started = False
        self.frame = object()

    def load_image(self, path):
        self.source_type = SourceType.IMAGE
        return self.frame

    def start_camera(self, index):
        self.camera_index = index
        self.source_type = SourceType.CAMERA

    def start_screen(self):
        self.screen_started = True
        self.source_type = SourceType.SCREEN

    def stop(self):
        self.stopped = True
        self.source_type = SourceType.NONE


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
    def process(self, frame, settings):
        return FrameResult(
            source_frame=frame,
            display_frame=frame,
            status=RuntimeStatus.READY,
            message=f"conf={settings.confidence}",
            stats=DefectStats(total=0, by_class={}),
        )


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


def test_stop_stops_runtime_and_capture():
    controller, capture, runtime = make_controller()
    controller.start_screen()

    controller.stop()

    assert runtime.is_running is False
    assert capture.stopped is True
    assert controller.get_status().status is RuntimeStatus.STOPPED
```

- [ ] **Step 2: Write runtime tests**

Create `tests/app/test_runtime.py`:

```python
import numpy as np

from app.runtime import ProcessingRuntime
from app.state import AppState
from domain import FrameResult, RuntimeStatus


class OneFrameCapture:
    def __init__(self):
        self.frames = [np.zeros((2, 2, 3), dtype=np.uint8)]
        self.stopped = False

    def read_frame(self):
        if self.frames:
            return self.frames.pop()
        return None

    def stop(self):
        self.stopped = True


class RecordingProcessor:
    def __init__(self):
        self.calls = 0

    def process(self, frame, settings):
        self.calls += 1
        return FrameResult(
            source_frame=frame,
            display_frame=frame,
            status=RuntimeStatus.READY,
            message="processed",
        )


def test_run_once_processes_frame_and_stores_latest_result():
    capture = OneFrameCapture()
    processor = RecordingProcessor()
    runtime = ProcessingRuntime(capture, processor, AppState())

    processed = runtime.run_once()

    assert processed is True
    assert processor.calls == 1
    assert runtime.poll_latest().message == "processed"


def test_run_once_returns_false_when_no_frame_available():
    capture = OneFrameCapture()
    capture.frames.clear()
    runtime = ProcessingRuntime(capture, RecordingProcessor(), AppState())

    processed = runtime.run_once()

    assert processed is False
    assert runtime.poll_latest() is None
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
pytest tests/app/test_controller.py tests/app/test_runtime.py -v
```

Expected: FAIL with import errors for `app.controller`.

- [ ] **Step 4: Implement app state**

Create `app/state.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from domain import AppMode, DefectStats, ProcessingSettings, RuntimeSnapshot, RuntimeStatus, SourceType


@dataclass
class AppState:
    settings: ProcessingSettings = field(default_factory=ProcessingSettings)
    status: RuntimeStatus = RuntimeStatus.IDLE
    source_type: SourceType = SourceType.NONE
    mode: AppMode = AppMode.DETECT
    message: str = "Ready"
    last_error: str | None = None
    stats: DefectStats = field(default_factory=DefectStats)

    def snapshot(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            status=self.status,
            source_type=self.source_type,
            mode=self.mode,
            message=self.message,
            settings=self.settings,
            stats=self.stats,
            last_error=self.last_error,
        )
```

- [ ] **Step 5: Implement runtime**

Create `app/runtime.py`:

```python
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
```

- [ ] **Step 6: Implement controller**

Create `app/controller.py`:

```python
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
```

- [ ] **Step 7: Export app classes**

Create `app/__init__.py`:

```python
from .controller import AppController
from .runtime import ProcessingRuntime
from .state import AppState

__all__ = ["AppController", "AppState", "ProcessingRuntime"]
```

- [ ] **Step 8: Run tests**

Run:

```bash
pytest tests/app/test_controller.py tests/app/test_runtime.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add app tests/app
git commit -m "feat: add app controller runtime"
```

---

### Task 6: Wire Backend Together

**Files:**
- Create: `app/factory.py`
- Modify: `app/__init__.py`
- Modify: `services/__init__.py`
- Create: `services/overlay_service.py`
- Test: `tests/app/test_factory.py`

- [ ] **Step 1: Write factory test**

Create `tests/app/test_factory.py`:

```python
from app import AppController
from app.factory import build_controller


class MissingModelConfig:
    MODEL_PATH = "missing-model-for-factory-test.pt"


def test_build_controller_returns_app_controller():
    controller = build_controller(MissingModelConfig())

    assert isinstance(controller, AppController)
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
pytest tests/app/test_factory.py -v
```

Expected: FAIL with import error for `app.factory`.

- [ ] **Step 3: Add overlay service**

Create `services/overlay_service.py`:

```python
from __future__ import annotations

from typing import Any


class OverlayService:
    """Owns visual overlay operations as the project grows."""

    def passthrough(self, frame: Any) -> Any:
        return frame
```

- [ ] **Step 4: Add app factory**

Create `app/factory.py`:

```python
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
```

- [ ] **Step 5: Update exports**

Replace `app/__init__.py` with:

```python
from .controller import AppController
from .factory import build_controller
from .runtime import ProcessingRuntime
from .state import AppState

__all__ = ["AppController", "AppState", "ProcessingRuntime", "build_controller"]
```

Replace `services/__init__.py` with:

```python
from .capture_service import CaptureService
from .defect_history import DefectHistory
from .detection_service import DetectionService
from .frame_processor import FrameProcessor
from .overlay_service import OverlayService

__all__ = [
    "CaptureService",
    "DefectHistory",
    "DetectionService",
    "FrameProcessor",
    "OverlayService",
]
```

- [ ] **Step 6: Run factory test**

Run:

```bash
pytest tests/app/test_factory.py -v
```

Expected: PASS. The test config points to a missing model path, so no real YOLO inference is run.

- [ ] **Step 7: Run backend tests**

Run:

```bash
pytest tests/domain tests/services tests/app -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add app services tests/app/test_factory.py
git commit -m "feat: wire backend controller factory"
```

---

### Task 7: Dear PyGui Frame Texture Adapter

**Files:**
- Create: `ui_dpg/__init__.py`
- Create: `ui_dpg/adapters/__init__.py`
- Create: `ui_dpg/adapters/frame_texture.py`
- Test: `tests/ui_dpg/test_frame_texture.py`

- [ ] **Step 1: Write adapter tests**

Create `tests/ui_dpg/test_frame_texture.py`:

```python
import numpy as np

from ui_dpg.adapters.frame_texture import bgr_frame_to_rgba_float, fit_size


def test_bgr_frame_to_rgba_float_converts_channels_and_range():
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    frame[0, 0] = [255, 128, 0]

    data = bgr_frame_to_rgba_float(frame)

    assert data == [0.0, 128 / 255.0, 1.0, 1.0]


def test_fit_size_preserves_aspect_ratio():
    assert fit_size(1920, 1080, 960, 540) == (960, 540)
    assert fit_size(1920, 1080, 500, 500) == (500, 281)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
pytest tests/ui_dpg/test_frame_texture.py -v
```

Expected: FAIL with import error for `ui_dpg`.

- [ ] **Step 3: Implement texture adapter**

Create `ui_dpg/__init__.py`:

```python
"""Dear PyGui user interface package."""
```

Create `ui_dpg/adapters/__init__.py`:

```python
from .frame_texture import bgr_frame_to_rgba_float, fit_size

__all__ = ["bgr_frame_to_rgba_float", "fit_size"]
```

Create `ui_dpg/adapters/frame_texture.py`:

```python
from __future__ import annotations

import cv2
import numpy as np


def fit_size(source_w: int, source_h: int, max_w: int, max_h: int) -> tuple[int, int]:
    if source_w <= 0 or source_h <= 0:
        return 1, 1
    scale = min(max_w / source_w, max_h / source_h)
    width = max(1, int(source_w * scale))
    height = max(1, int(source_h * scale))
    return width, height


def bgr_frame_to_rgba_float(frame: np.ndarray) -> list[float]:
    rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    return (rgba.astype(np.float32) / 255.0).ravel().tolist()


def resize_for_texture(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
```

- [ ] **Step 4: Run tests**

Run:

```bash
pytest tests/ui_dpg/test_frame_texture.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui_dpg tests/ui_dpg/test_frame_texture.py
git commit -m "feat: add dpg frame texture adapter"
```

---

### Task 8: Dear PyGui MVP Views and Entry Point

**Files:**
- Create: `ui_dpg/views/__init__.py`
- Create: `ui_dpg/views/control_panel.py`
- Create: `ui_dpg/views/viewport.py`
- Create: `ui_dpg/views/defects_panel.py`
- Create: `ui_dpg/views/status_bar.py`
- Create: `ui_dpg/app.py`
- Create: `main_dpg.py`

- [ ] **Step 1: Create view package**

Create `ui_dpg/views/__init__.py`:

```python
"""Dear PyGui view helpers."""
```

- [ ] **Step 2: Implement control panel view**

Create `ui_dpg/views/control_panel.py`:

```python
from __future__ import annotations

import dearpygui.dearpygui as dpg


class ControlPanelView:
    def __init__(self, controller, on_load_image, on_start_screen, on_start_camera, on_stop):
        self._controller = controller
        self._on_load_image = on_load_image
        self._on_start_screen = on_start_screen
        self._on_start_camera = on_start_camera
        self._on_stop = on_stop

    def build(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(label="Load Image", callback=lambda: self._on_load_image())
            dpg.add_button(label="Screen", callback=lambda: self._on_start_screen())
            dpg.add_button(label="Camera 0", callback=lambda: self._on_start_camera(0))
            dpg.add_button(label="Stop", callback=lambda: self._on_stop())
            dpg.add_text("Confidence")
            dpg.add_slider_float(
                tag="confidence_slider",
                default_value=0.3,
                min_value=0.1,
                max_value=0.9,
                width=160,
                callback=lambda sender, value: self._controller.set_confidence(value),
            )
```

- [ ] **Step 3: Implement viewport view**

Create `ui_dpg/views/viewport.py`:

```python
from __future__ import annotations

import dearpygui.dearpygui as dpg

from ui_dpg.adapters.frame_texture import bgr_frame_to_rgba_float, fit_size, resize_for_texture


class ViewportView:
    def __init__(self, texture_tag: str = "frame_texture", image_tag: str = "frame_image"):
        self.texture_tag = texture_tag
        self.image_tag = image_tag
        self._width = 640
        self._height = 360

    def build(self) -> None:
        with dpg.texture_registry():
            dpg.add_dynamic_texture(self._width, self._height, [0.0] * self._width * self._height * 4, tag=self.texture_tag)
        dpg.add_image(self.texture_tag, tag=self.image_tag)

    def update_frame(self, frame) -> None:
        if frame is None:
            return
        height, width = frame.shape[:2]
        new_width, new_height = fit_size(width, height, 960, 540)
        resized = resize_for_texture(frame, new_width, new_height)
        data = bgr_frame_to_rgba_float(resized)

        if new_width != self._width or new_height != self._height:
            self._width = new_width
            self._height = new_height
            dpg.delete_item(self.image_tag)
            dpg.delete_item(self.texture_tag)
            with dpg.texture_registry():
                dpg.add_dynamic_texture(self._width, self._height, data, tag=self.texture_tag)
            dpg.add_image(self.texture_tag, tag=self.image_tag)
        else:
            dpg.set_value(self.texture_tag, data)
```

- [ ] **Step 4: Implement defects panel view**

Create `ui_dpg/views/defects_panel.py`:

```python
from __future__ import annotations

from datetime import datetime

import dearpygui.dearpygui as dpg


class DefectsPanelView:
    def __init__(self):
        self._rows: list[str] = []

    def build(self) -> None:
        dpg.add_text("Detected Defects")
        dpg.add_text("Total: 0", tag="defects_total")
        dpg.add_text("By Class: none", tag="defects_by_class")
        with dpg.child_window(width=320, height=460, border=True):
            dpg.add_listbox(tag="defects_list", items=[], width=300, num_items=20)

    def update(self, detections, stats) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        for detection in detections:
            self._rows.insert(0, f"[{timestamp}] {detection.class_name} ({detection.confidence:.2f})")
        self._rows = self._rows[:100]
        by_class = ", ".join(f"{name}: {count}" for name, count in stats.by_class.items()) or "none"
        dpg.set_value("defects_total", f"Total: {stats.total}")
        dpg.set_value("defects_by_class", f"By Class: {by_class}")
        dpg.configure_item("defects_list", items=self._rows)
```

- [ ] **Step 5: Implement status bar view**

Create `ui_dpg/views/status_bar.py`:

```python
from __future__ import annotations

import dearpygui.dearpygui as dpg


class StatusBarView:
    def build(self) -> None:
        dpg.add_text("Status: Ready", tag="status_text")

    def update(self, snapshot) -> None:
        text = f"Status: {snapshot.status.value} | {snapshot.message}"
        dpg.set_value("status_text", text)
```

- [ ] **Step 6: Implement DPG app**

Create `ui_dpg/app.py`:

```python
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog

import dearpygui.dearpygui as dpg

from app.factory import build_controller
from core.config import Config
from ui_dpg.views.control_panel import ControlPanelView
from ui_dpg.views.defects_panel import DefectsPanelView
from ui_dpg.views.status_bar import StatusBarView
from ui_dpg.views.viewport import ViewportView


class DearPyGuiApp:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.controller = build_controller(self.config)
        self.viewport = ViewportView()
        self.defects = DefectsPanelView()
        self.status = StatusBarView()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Wire Defect Detector", width=self.config.WINDOW_WIDTH, height=self.config.WINDOW_HEIGHT)
        self._build()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self._update()
            dpg.render_dearpygui_frame()

        self.controller.stop()
        dpg.destroy_context()

    def _build(self) -> None:
        with dpg.window(label="Wire Defect Detector", tag="main_window", width=self.config.WINDOW_WIDTH, height=self.config.WINDOW_HEIGHT):
            ControlPanelView(
                self.controller,
                self._load_image,
                self.controller.start_screen,
                self.controller.start_camera,
                self.controller.stop,
            ).build()
            with dpg.group(horizontal=True):
                with dpg.child_window(width=980, height=590, border=True):
                    self.viewport.build()
                with dpg.child_window(width=340, height=590, border=True):
                    self.defects.build()
            self.status.build()

    def _load_image(self) -> None:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")],
        )
        root.destroy()
        if path:
            self.controller.load_image(path)

    def _update(self) -> None:
        result = self.controller.poll_latest_frame()
        if result is not None:
            self.viewport.update_frame(result.display_frame)
            self.defects.update(result.detections, result.stats)
        self.status.update(self.controller.get_status())


def run_app() -> None:
    DearPyGuiApp().run()
```

- [ ] **Step 7: Implement entry point**

Create `main_dpg.py`:

```python
from ui_dpg.app import run_app


if __name__ == "__main__":
    run_app()
```

- [ ] **Step 8: Run import checks**

Run:

```bash
python -m py_compile main_dpg.py ui_dpg/app.py ui_dpg/views/control_panel.py ui_dpg/views/viewport.py ui_dpg/views/defects_panel.py ui_dpg/views/status_bar.py
```

Expected: exits with code 0.

- [ ] **Step 9: Run backend and adapter tests**

Run:

```bash
pytest tests/domain tests/services tests/app tests/ui_dpg -v
```

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add main_dpg.py ui_dpg tests/ui_dpg
git commit -m "feat: add dearpygui detection mvp"
```

---

### Task 9: Documentation Update and Verification

**Files:**
- Modify: `architecrute.md`
- Modify: `docs/modules/app.md`
- Modify: `docs/modules/services.md`
- Modify: `docs/modules/domain.md`
- Modify: `docs/modules/ui_dpg.md`
- Modify: `README.md`

- [ ] **Step 1: Update architecture note**

Add this section to `architecrute.md`:

```markdown
## Dear PyGui Migration Path

The project now has a backend-first architecture for the DPG UI:

- `domain/` defines dataclasses and enums shared across layers.
- `services/` owns detection, frame processing, capture switching, and defect history.
- `app/` exposes a thin `AppController` and runtime loop for UI code.
- `ui_dpg/` renders the Dear PyGui MVP and calls only `AppController`.

The first DPG MVP is started with:

```bash
python main_dpg.py
```

The Tkinter entry point remains `python main.py` while migration is in progress.
```

- [ ] **Step 2: Update README quick start**

Add this section to `README.md` near the GUI launch section:

```markdown
### Dear PyGui MVP

The DPG migration entry point is:

```bash
python main_dpg.py
```

Current DPG scope:

- load image;
- screen capture;
- camera 0 capture;
- YOLO inference;
- confidence slider;
- defect history and class statistics;
- status display.

Calibration and measurement are still handled by the existing Tkinter workflow until the next migration phase.
```

- [ ] **Step 3: Run verification commands**

Run:

```bash
pytest tests/domain tests/services tests/app tests/ui_dpg -v
python -m py_compile main_dpg.py
git status --short
```

Expected:

- pytest exits with code 0;
- py_compile exits with code 0;
- `git status --short` shows only the documentation files changed before commit.

- [ ] **Step 4: Commit**

```bash
git add architecrute.md README.md docs/modules
git commit -m "docs: document dearpygui backend architecture"
```

---

## Final Manual Verification

Run:

```bash
python main_dpg.py
```

Verify:

- the DPG window opens;
- `Load Image` opens a file picker;
- selecting a sample image displays the annotated frame;
- defect history updates when detections are returned;
- confidence slider changes the value used by subsequent processing;
- `Screen` starts screen capture without freezing the UI;
- `Camera 0` starts camera capture if a camera is available;
- `Stop` stops live processing;
- closing the DPG window stops runtime cleanly.

If a machine has no camera, camera verification can be recorded as skipped with reason `no local camera available`.
