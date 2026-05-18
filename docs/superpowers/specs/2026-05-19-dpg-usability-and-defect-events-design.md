# DPG Usability and Defect Events Design

Date: 2026-05-19

## Goal

Improve the Dear PyGui MVP usability without changing the backend-first architecture:

- make the source controls easier to read and click;
- show the active input source near runtime status;
- replace the unclear hard-coded camera button with a camera selector;
- stop camera/screen detections from counting the same physical defect on every frame;
- add a few small diagnostics that help manual testing and future debugging.

## Current Context

The DPG MVP runs from `main_dpg.py` in the `feat/dpg-migration` worktree. The UI talks to `AppController`; services own source lifecycle, detection, frame processing, and defect history. `DefectHistory` currently counts every `Detection` passed by `FrameProcessor`, so live video sources can inflate totals while the same defect remains visible.

## Decisions

### Source Controls

The control panel stays as a single horizontal toolbar. Buttons become larger and get stable dimensions. The active source button is highlighted green based on `RuntimeSnapshot.source_type`; `Stop` is styled red. The source state is also shown in the status bar as `Source: image`, `Source: camera`, `Source: screen`, or `Source: none`.

### Camera Selection

The first version uses a compact combo box beside a `Camera` button instead of a separate modal window. A `Refresh` button probes a small camera index range and updates the combo. If no cameras are found, the combo still exposes `0` as a fallback because many Windows setups only initialize the camera when the user actually starts capture.

### Defect Event Deduplication

Counting moves from raw frame detections to deduplicated defect events.

A detection is treated as the same event when:

- `class_name` matches;
- bounding boxes overlap with IoU at or above `0.4`;
- the previous matching event was seen within `2.0` seconds.

Repeats refresh the event timestamp so a defect that stays in the same place is counted once until it disappears long enough or moves enough. The annotated image still shows all current YOLO detections. Statistics and the defect list receive only new events.

To keep this explicit, `FrameResult` gains `new_detections`. Existing `detections` remains the complete current-frame detection list.

### Small Usability Improvements

Add a `Clear` button to reset defect history. Show last frame processing time in the status area when available. If camera start fails, the status should show an error and the camera button should not remain active.

## Components

- `services.defect_event_filter.DefectEventFilter`: pure service that receives current detections and returns only new defect events.
- `services.frame_processor.FrameProcessor`: uses `DefectEventFilter`; adds only `new_detections` to `DefectHistory`.
- `domain.models.FrameResult`: adds `new_detections`.
- `services.capture_service.CaptureService`: exposes `available_cameras()`.
- `app.controller.AppController`: exposes `list_cameras()` and `clear_defects()`, and handles live source start errors consistently.
- `ui_dpg.views.control_panel.ControlPanelView`: larger buttons, camera combo, active-source styling, clear action.
- `ui_dpg.views.status_bar.StatusBarView`: status, source, and processing time.
- `ui_dpg.views.defects_panel.DefectsPanelView`: renders only new events and supports clear.

## Testing

Core tests should cover:

- IoU calculation and event deduplication behavior;
- frame processing adds only new events to history while preserving current detections;
- controller camera listing, source error handling, and clear action;
- capture service camera probing with injected probes.

DPG-specific behavior is checked with import/compile tests and manual smoke testing. No real YOLO model, camera, or GUI automation is required for automated tests.

## Manual Smoke Test

Run from the worktree:

```powershell
..\..\.venv\Scripts\python.exe main_dpg.py
```

Check:

- buttons are larger and readable;
- active source button turns green;
- `Stop` is red;
- status bar shows source and processing time;
- camera combo is understandable and refreshable;
- camera/screen defect totals do not increase every frame for the same stable defect;
- `Clear` resets the defect list and counters;
- image, screen, camera, and stop still work as before.
