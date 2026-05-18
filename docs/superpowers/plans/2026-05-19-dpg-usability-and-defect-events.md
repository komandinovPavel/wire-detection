# DPG Usability and Defect Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the DPG toolbar/status usability and count stable live-video defects as deduplicated events instead of one new defect per frame.

**Architecture:** Keep UI thin: DPG renders state and calls `AppController`; backend services own camera probing, defect event filtering, history, and frame processing. `FrameResult.detections` remains all current-frame detections, while new `FrameResult.new_detections` drives history/list updates.

**Tech Stack:** Python, Dear PyGui, NumPy/OpenCV, pytest, existing app/services/domain layers.

---

## Scope Check

This plan implements the agreed next DPG usability pass from `docs/superpowers/specs/2026-05-19-dpg-usability-and-defect-events-design.md`. It does not migrate calibration or measurement and does not add full GUI automation.

## File Map

- Modify `domain/models.py`: add `FrameResult.new_detections`.
- Create `services/defect_event_filter.py`: IoU and event deduplication.
- Modify `services/frame_processor.py`: add only new events to history.
- Modify `services/capture_service.py`: camera index probing.
- Modify `services/__init__.py`: export new service.
- Modify `app/controller.py`: camera listing, clear defects, safer live-source error handling.
- Modify `ui_dpg/app.py`: wire updated view callbacks and use `new_detections`.
- Modify `ui_dpg/views/control_panel.py`: larger controls, camera combo, active themes, clear button.
- Modify `ui_dpg/views/status_bar.py`: source and processing time display.
- Modify `ui_dpg/views/defects_panel.py`: clear rows support.
- Modify `docs/modules/services.md`, `docs/modules/app.md`, `docs/modules/ui_dpg.md`: describe the new responsibilities.
- Create or modify tests in `tests/domain`, `tests/services`, and `tests/app`.

---

### Task 1: Add Defect Event Filtering

**Files:**
- Modify: `domain/models.py`
- Create: `services/defect_event_filter.py`
- Modify: `services/__init__.py`
- Test: `tests/domain/test_models.py`
- Test: `tests/services/test_defect_event_filter.py`

- [ ] **Step 1: Write the failing domain test**

Add to `tests/domain/test_models.py`:

```python
from domain import Detection, FrameResult


def test_frame_result_separates_current_detections_from_new_events():
    current = [Detection("scratch", 0.9, (1, 1, 10, 10))]
    new_events = [Detection("scratch", 0.9, (1, 1, 10, 10))]

    result = FrameResult(detections=current, new_detections=new_events)

    assert result.detections is current
    assert result.new_detections is new_events
```

- [ ] **Step 2: Write the failing filter tests**

Create `tests/services/test_defect_event_filter.py`:

```python
from domain import Detection
from services.defect_event_filter import DefectEventFilter, bbox_iou


def detection(name="scratch", bbox=(0, 0, 10, 10), timestamp=1.0):
    return Detection(name, 0.9, bbox, timestamp=timestamp)


def test_bbox_iou_returns_overlap_ratio():
    assert bbox_iou((0, 0, 10, 10), (5, 5, 15, 15)) == 25 / 175


def test_first_detection_is_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)

    result = event_filter.filter_new([detection(timestamp=10.0)], now=10.0)

    assert len(result) == 1


def test_same_class_same_area_inside_window_is_not_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    event_filter.filter_new([detection(timestamp=10.0)], now=10.0)

    result = event_filter.filter_new([detection(bbox=(1, 1, 11, 11), timestamp=11.0)], now=11.0)

    assert result == []


def test_same_area_after_window_is_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    event_filter.filter_new([detection(timestamp=10.0)], now=10.0)

    result = event_filter.filter_new([detection(timestamp=13.1)], now=13.1)

    assert len(result) == 1


def test_different_class_or_far_bbox_is_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    event_filter.filter_new([detection("scratch", timestamp=10.0)], now=10.0)

    different_class = event_filter.filter_new([detection("crack", timestamp=10.5)], now=10.5)
    far_bbox = event_filter.filter_new([detection("scratch", bbox=(50, 50, 60, 60), timestamp=10.7)], now=10.7)

    assert len(different_class) == 1
    assert len(far_bbox) == 1
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/domain/test_models.py tests/services/test_defect_event_filter.py -q
```

Expected: FAIL because `FrameResult.new_detections` and `services.defect_event_filter` do not exist.

- [ ] **Step 4: Add `new_detections` to `FrameResult`**

In `domain/models.py`, update `FrameResult`:

```python
@dataclass(frozen=True)
class FrameResult:
    source_frame: Any = None
    display_frame: Any = None
    detections: list[Detection] = field(default_factory=list)
    new_detections: list[Detection] = field(default_factory=list)
    stats: DefectStats = field(default_factory=DefectStats)
    status: RuntimeStatus = RuntimeStatus.READY
    message: str = ""
    error: str | None = None
    processing_ms: float = 0.0
```

Leave `FrameResult.error()` with the default empty `new_detections`.

- [ ] **Step 5: Implement the filter**

Create `services/defect_event_filter.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Sequence

from domain import Detection


def bbox_iou(left: Sequence[float], right: Sequence[float]) -> float:
    left_x1, left_y1, left_x2, left_y2 = left
    right_x1, right_y1, right_x2, right_y2 = right

    inter_x1 = max(left_x1, right_x1)
    inter_y1 = max(left_y1, right_y1)
    inter_x2 = min(left_x2, right_x2)
    inter_y2 = min(left_y2, right_y2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h

    left_area = max(0.0, left_x2 - left_x1) * max(0.0, left_y2 - left_y1)
    right_area = max(0.0, right_x2 - right_x1) * max(0.0, right_y2 - right_y1)
    union = left_area + right_area - intersection
    if union <= 0:
        return 0.0
    return intersection / union


@dataclass
class _TrackedEvent:
    detection: Detection
    last_seen: float


class DefectEventFilter:
    """Converts per-frame detections into deduplicated defect events."""

    def __init__(self, iou_threshold: float = 0.4, window_seconds: float = 2.0):
        self._iou_threshold = iou_threshold
        self._window_seconds = window_seconds
        self._events: list[_TrackedEvent] = []

    def filter_new(self, detections: list[Detection], now: float | None = None) -> list[Detection]:
        now = perf_counter() if now is None else now
        self._events = [
            event for event in self._events
            if now - event.last_seen <= self._window_seconds
        ]

        new_events: list[Detection] = []
        for detection in detections:
            match = self._find_match(detection, now)
            if match is None:
                self._events.append(_TrackedEvent(detection=detection, last_seen=now))
                new_events.append(detection)
            else:
                match.detection = detection
                match.last_seen = now
        return new_events

    def clear(self) -> None:
        self._events.clear()

    def _find_match(self, detection: Detection, now: float) -> _TrackedEvent | None:
        for event in self._events:
            if now - event.last_seen > self._window_seconds:
                continue
            if event.detection.class_name != detection.class_name:
                continue
            if bbox_iou(event.detection.bbox, detection.bbox) >= self._iou_threshold:
                return event
        return None
```

- [ ] **Step 6: Export the filter**

Update `services/__init__.py`:

```python
from .defect_event_filter import DefectEventFilter
```

Add `"DefectEventFilter"` to `__all__`.

- [ ] **Step 7: Run tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/domain/test_models.py tests/services/test_defect_event_filter.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add domain/models.py services/__init__.py services/defect_event_filter.py tests/domain/test_models.py tests/services/test_defect_event_filter.py
git commit -m "feat: add defect event filter"
```

---

### Task 2: Count Only New Events in Frame Processing

**Files:**
- Modify: `services/frame_processor.py`
- Test: `tests/services/test_frame_processor.py`

- [ ] **Step 1: Update failing frame processor tests**

Add to `tests/services/test_frame_processor.py`:

```python
from services.defect_event_filter import DefectEventFilter


class StableDetectionService:
    def detect(self, frame, settings):
        return DetectionResult(
            annotated_frame=frame,
            detections=[Detection("scratch", 0.9, (0, 0, 10, 10), timestamp=10.0)],
        )


def test_process_preserves_current_detections_but_counts_only_new_events():
    frame = np.zeros((3, 3, 3), dtype=np.uint8)
    history = DefectHistory()
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    processor = FrameProcessor(StableDetectionService(), history, event_filter)

    first = processor.process(frame, ProcessingSettings())
    second = processor.process(frame, ProcessingSettings())

    assert len(first.detections) == 1
    assert len(first.new_detections) == 1
    assert len(second.detections) == 1
    assert second.new_detections == []
    assert second.stats.total == 1
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/services/test_frame_processor.py -q
```

Expected: FAIL because `FrameProcessor` does not accept an event filter and does not populate `new_detections`.

- [ ] **Step 3: Update `FrameProcessor`**

Modify `services/frame_processor.py`:

```python
from services.defect_event_filter import DefectEventFilter
```

Update constructor and success path:

```python
class FrameProcessor:
    """Use case for processing exactly one source frame."""

    def __init__(
        self,
        detection_service: DetectionService,
        history: DefectHistory,
        event_filter: DefectEventFilter | None = None,
    ):
        self._detection_service = detection_service
        self._history = history
        self._event_filter = event_filter or DefectEventFilter()

    def clear_history(self) -> None:
        self._history.clear()
        self._event_filter.clear()
```

In the non-error branch:

```python
new_detections = self._event_filter.filter_new(detection_result.detections)
self._history.add(new_detections)
return FrameResult(
    source_frame=frame,
    display_frame=detection_result.annotated_frame,
    detections=detection_result.detections,
    new_detections=new_detections,
    stats=self._history.stats(),
    status=RuntimeStatus.READY,
    message=f"Detections: {len(detection_result.detections)} | New: {len(new_detections)}",
    processing_ms=elapsed_ms,
)
```

- [ ] **Step 4: Run frame processor tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/services/test_frame_processor.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add services/frame_processor.py tests/services/test_frame_processor.py
git commit -m "feat: count deduplicated defect events"
```

---

### Task 3: Add Camera Discovery and Controller Commands

**Files:**
- Modify: `services/capture_service.py`
- Modify: `app/controller.py`
- Test: `tests/services/test_capture_service.py`
- Test: `tests/app/test_controller.py`

- [ ] **Step 1: Write capture service tests**

Add to `tests/services/test_capture_service.py`:

```python
def test_available_cameras_uses_probe_and_returns_detected_indices():
    service = CaptureService(camera_probe=lambda index: index in {0, 2})

    assert service.available_cameras(max_index=4) == [0, 2]


def test_available_cameras_falls_back_to_zero_when_no_camera_is_detected():
    service = CaptureService(camera_probe=lambda index: False)

    assert service.available_cameras(max_index=4) == [0]
```

- [ ] **Step 2: Write controller tests**

Add to `tests/app/test_controller.py`:

```python
def test_list_cameras_delegates_to_capture_service():
    controller, capture, _ = make_controller()
    capture.available = [0, 2]

    assert controller.list_cameras() == [0, 2]


def test_clear_defects_resets_processor_history_and_state_stats():
    controller, _, _ = make_controller()
    controller.clear_defects()

    assert controller.get_status().stats.total == 0


def test_start_camera_failure_sets_error_status_without_starting_runtime():
    controller, capture, runtime = make_controller()
    capture.raise_on_camera = True

    controller.start_camera(3)

    assert runtime.is_running is False
    assert controller.get_status().status is RuntimeStatus.ERROR
    assert "Camera" in controller.get_status().message
```

Extend `StubCaptureService` in the same file:

```python
self.available = [0]
self.raise_on_camera = False
```

Update `start_camera`:

```python
if self.raise_on_camera:
    raise RuntimeError(f"Camera {index} failed")
```

Add:

```python
def available_cameras(self, max_index=5):
    return self.available
```

Extend `StubProcessor`:

```python
def clear_history(self):
    self.cleared = True
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/services/test_capture_service.py tests/app/test_controller.py -q
```

Expected: FAIL because `camera_probe`, `available_cameras`, `list_cameras`, and `clear_defects` do not exist yet.

- [ ] **Step 4: Implement camera discovery**

Modify `services/capture_service.py`:

```python
import cv2
```

Update constructor:

```python
camera_probe: Callable[[int], bool] | None = None,
```

Store:

```python
self._camera_probe = camera_probe or self._probe_camera
```

Add:

```python
def available_cameras(self, max_index: int = 5) -> list[int]:
    detected = [index for index in range(max_index) if self._camera_probe(index)]
    return detected or [0]

def _probe_camera(self, index: int) -> bool:
    capture = cv2.VideoCapture(index)
    try:
        return bool(capture.isOpened())
    finally:
        capture.release()
```

- [ ] **Step 5: Implement controller commands**

Modify `app/controller.py`:

```python
def list_cameras(self, max_index: int = 5) -> list[int]:
    return self._capture_service.available_cameras(max_index)

def clear_defects(self) -> None:
    self._frame_processor.clear_history()
    self._state.stats = self._frame_processor.stats()
```

If `FrameProcessor.stats()` does not exist, add it:

```python
def stats(self):
    return self._history.stats()
```

Wrap `start_camera()` and `start_screen()` in `try/except` so failed source startup sets:

```python
self._state.source_type = self._capture_service.source_type
self._state.status = RuntimeStatus.ERROR
self._state.message = str(exc)
self._state.last_error = str(exc)
```

and does not call `self._runtime.start()`.

- [ ] **Step 6: Run tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/services/test_capture_service.py tests/app/test_controller.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add services/capture_service.py services/frame_processor.py app/controller.py tests/services/test_capture_service.py tests/app/test_controller.py
git commit -m "feat: add camera discovery and controller commands"
```

---

### Task 4: Improve Control Panel and Status Bar

**Files:**
- Modify: `ui_dpg/views/control_panel.py`
- Modify: `ui_dpg/views/status_bar.py`
- Modify: `ui_dpg/app.py`

- [ ] **Step 1: Update `ControlPanelView` shape**

Modify `ui_dpg/views/control_panel.py` so the constructor accepts:

```python
def __init__(
    self,
    controller,
    on_load_image,
    on_start_screen,
    on_start_camera,
    on_stop,
    on_clear_defects,
):
```

Add stable tags:

```python
IMAGE_BUTTON = "source_image_button"
SCREEN_BUTTON = "source_screen_button"
CAMERA_BUTTON = "source_camera_button"
STOP_BUTTON = "stop_button"
CLEAR_BUTTON = "clear_defects_button"
CAMERA_COMBO = "camera_combo"
```

- [ ] **Step 2: Add themes and larger widgets**

In `build()`, create themes once and set larger dimensions:

```python
self._build_themes()
with dpg.group(horizontal=True):
    dpg.add_button(tag=self.IMAGE_BUTTON, label="Image", width=112, height=36, callback=lambda: self._on_load_image())
    dpg.add_button(tag=self.SCREEN_BUTTON, label="Screen", width=112, height=36, callback=lambda: self._on_start_screen())
    dpg.add_combo(tag=self.CAMERA_COMBO, items=["0"], default_value="0", width=72)
    dpg.add_button(tag=self.CAMERA_BUTTON, label="Camera", width=112, height=36, callback=lambda: self._start_selected_camera())
    dpg.add_button(label="Refresh", width=90, height=36, callback=lambda: self.refresh_cameras())
    dpg.add_button(tag=self.STOP_BUTTON, label="Stop", width=100, height=36, callback=lambda: self._on_stop())
    dpg.add_button(tag=self.CLEAR_BUTTON, label="Clear", width=100, height=36, callback=lambda: self._on_clear_defects())
    dpg.add_text("Confidence")
    dpg.add_slider_float(tag="confidence_slider", default_value=0.3, min_value=0.1, max_value=0.9, width=180, callback=lambda sender, value: self._controller.set_confidence(value))
```

Add helper methods:

```python
def refresh_cameras(self) -> None:
    cameras = [str(index) for index in self._controller.list_cameras()]
    dpg.configure_item(self.CAMERA_COMBO, items=cameras)
    dpg.set_value(self.CAMERA_COMBO, cameras[0])

def _start_selected_camera(self) -> None:
    value = dpg.get_value(self.CAMERA_COMBO)
    self._on_start_camera(int(value))
```

Create `_build_themes()` with normal, active green, and red stop button themes using `dpg.add_theme_color(dpg.mvThemeCol_Button, ...)`.

- [ ] **Step 3: Add source highlight update**

Add:

```python
def update(self, snapshot) -> None:
    active_tag = {
        "image": self.IMAGE_BUTTON,
        "screen": self.SCREEN_BUTTON,
        "camera": self.CAMERA_BUTTON,
    }.get(snapshot.source_type.value)
    for tag in [self.IMAGE_BUTTON, self.SCREEN_BUTTON, self.CAMERA_BUTTON]:
        dpg.bind_item_theme(tag, "active_source_theme" if tag == active_tag else "normal_button_theme")
    dpg.bind_item_theme(self.STOP_BUTTON, "stop_button_theme")
```

- [ ] **Step 4: Update status bar**

Modify `ui_dpg/views/status_bar.py`:

```python
class StatusBarView:
    def build(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_text("Status: Ready", tag="status_text")
            dpg.add_text("Source: none", tag="source_text")
            dpg.add_text("Frame: -- ms", tag="frame_time_text")

    def update(self, snapshot, frame_result=None) -> None:
        dpg.set_value("status_text", f"Status: {snapshot.status.value} | {snapshot.message}")
        dpg.set_value("source_text", f"Source: {snapshot.source_type.value}")
        if frame_result is None:
            dpg.set_value("frame_time_text", "Frame: -- ms")
        else:
            dpg.set_value("frame_time_text", f"Frame: {frame_result.processing_ms:.1f} ms")
```

- [ ] **Step 5: Wire app callbacks**

Modify `ui_dpg/app.py`:

```python
self.controls = ControlPanelView(...)
```

Pass `self.controller.clear_defects` to the view. In `_build()`, call `self.controls.build()` instead of creating an unnamed control panel. In `_update()`:

```python
snapshot = self.controller.get_status()
self.controls.update(snapshot)
self.status.update(snapshot, result)
```

Use `result.new_detections` for the defects panel:

```python
self.defects.update(result.new_detections, result.stats)
```

- [ ] **Step 6: Run compile check**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m py_compile ui_dpg/app.py ui_dpg/views/control_panel.py ui_dpg/views/status_bar.py
```

Expected: exit code `0`.

- [ ] **Step 7: Commit**

```powershell
git add ui_dpg/app.py ui_dpg/views/control_panel.py ui_dpg/views/status_bar.py
git commit -m "feat: improve dpg source controls"
```

---

### Task 5: Clear Defect List and Use New Events in UI

**Files:**
- Modify: `ui_dpg/views/defects_panel.py`
- Modify: `ui_dpg/app.py`

- [ ] **Step 1: Add clear support to defects panel**

Modify `ui_dpg/views/defects_panel.py`:

```python
def clear(self) -> None:
    self._rows.clear()
    dpg.set_value("defects_total", "Total: 0")
    dpg.set_value("defects_by_class", "By Class: none")
    dpg.configure_item("defects_list", items=[])
```

- [ ] **Step 2: Route clear callback through the app**

In `ui_dpg/app.py`, add:

```python
def _clear_defects(self) -> None:
    self.controller.clear_defects()
    self.defects.clear()
```

Pass `self._clear_defects` to `ControlPanelView`.

- [ ] **Step 3: Confirm defects update uses event list**

In `_update()`, keep:

```python
self.defects.update(result.new_detections, result.stats)
```

This ensures stable per-frame detections do not append repeated rows.

- [ ] **Step 4: Run compile check**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m py_compile ui_dpg/app.py ui_dpg/views/defects_panel.py
```

Expected: exit code `0`.

- [ ] **Step 5: Commit**

```powershell
git add ui_dpg/app.py ui_dpg/views/defects_panel.py
git commit -m "feat: add defect history clear action"
```

---

### Task 6: Documentation and Verification

**Files:**
- Modify: `docs/modules/services.md`
- Modify: `docs/modules/app.md`
- Modify: `docs/modules/ui_dpg.md`
- Modify: `docs/superpowers/checkpoints/2026-05-19-dpg-migration-handoff.md`

- [ ] **Step 1: Update module docs**

Update docs with these facts:

```markdown
- `DefectEventFilter`: turns repeated live-frame detections into deduplicated defect events.
- `FrameResult.detections` means current-frame detections.
- `FrameResult.new_detections` means detections that should increment history/statistics.
- `ControlPanelView` owns source button styling and camera combo rendering.
- `StatusBarView` shows runtime status, active source, and latest frame processing time.
```

- [ ] **Step 2: Update handoff**

Append a new section to `docs/superpowers/checkpoints/2026-05-19-dpg-migration-handoff.md`:

```markdown
## Next Usability Plan

Created:

- `docs/superpowers/specs/2026-05-19-dpg-usability-and-defect-events-design.md`
- `docs/superpowers/plans/2026-05-19-dpg-usability-and-defect-events.md`

Planned work:

- larger source controls;
- active source and red stop styling;
- status source and frame-time display;
- camera combo plus refresh;
- deduplicated defect events using class + bbox IoU + time window;
- clear defect history action.
```

- [ ] **Step 3: Run automated verification**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/domain tests/services tests/app tests/ui_dpg -q
..\..\.venv\Scripts\python.exe -m py_compile main_dpg.py ui_dpg/app.py ui_dpg/views/control_panel.py ui_dpg/views/status_bar.py ui_dpg/views/defects_panel.py
```

Expected:

```text
all tests pass
py_compile exits with code 0
```

- [ ] **Step 4: Manual smoke test**

Run:

```powershell
..\..\.venv\Scripts\python.exe main_dpg.py
```

Check:

- source buttons are larger;
- selected source button is green;
- `Stop` is red;
- status bar shows `Source: ...`;
- camera combo is clear and refreshable;
- repeated stable camera/screen defects do not spam totals;
- `Clear` resets list and stats;
- window resizing still keeps viewport and right panel usable.

- [ ] **Step 5: Commit**

```powershell
git add docs/modules docs/superpowers/checkpoints/2026-05-19-dpg-migration-handoff.md
git commit -m "docs: update dpg usability handoff"
```

---

## Execution Notes

- Use the existing worktree: `E:\Code\Horev\wire-detection\.worktrees\dpg-migration`.
- Use the shared venv from the main checkout: `..\..\.venv\Scripts\python.exe`.
- Because this worktree may trigger Git safe-directory checks under Codex sandboxing, use:

```powershell
git -c safe.directory=E:/Code/Horev/wire-detection/.worktrees/dpg-migration status --short
```

for git inspection when needed.

## Final Quality Gate

Before calling the work complete, run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/domain tests/services tests/app tests/ui_dpg -q
..\..\.venv\Scripts\python.exe -m py_compile main_dpg.py ui_dpg/app.py ui_dpg/views/control_panel.py ui_dpg/views/status_bar.py ui_dpg/views/defects_panel.py
```

Expected: tests pass and compile check exits with code `0`.
