# Services Module

The `services` layer contains backend use cases and reusable application logic.

## Responsibilities

- Process frames.
- Run detection through a model adapter.
- Manage capture source selection.
- Track defect history and statistics.
- Turn repeated live-frame detections into deduplicated defect events.
- Provide overlay-related operations for future calibration and measurement UI.

## Current Classes

- `DetectionService`: typed adapter around `core.model.DefectDetector`.
- `CaptureService`: creates, switches, stops, and probes image/screen/camera sources.
- `FrameProcessor`: processes one frame with current settings and adds only new defect events to history.
- `DefectEventFilter`: deduplicates stable live detections by class, bbox IoU, and time window.
- `DefectHistory`: stores recent detections and class counts.
- `OverlayService`: pass-through overlay home for later calibration and measurement drawing.

## Detection Event Semantics

- `FrameResult.detections` means all detections visible in the current processed frame.
- `FrameResult.new_detections` means detections that should increment history/statistics.
- The UI can still render all current detections while counters avoid per-frame spam from one stable defect.

## Dependencies

Services can depend on `domain`, `core`, and `capture`. They should not depend on UI frameworks.

## Does Not Belong Here

- Dear PyGui widgets.
- Tkinter callbacks.
- Long-running UI loops.
- Training scripts.

