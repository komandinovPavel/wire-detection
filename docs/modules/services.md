# Services Module

The `services` layer contains backend use cases and reusable application logic.

## Responsibilities

- Process frames.
- Run detection through a model adapter.
- Manage capture source selection.
- Track defect history and statistics.
- Provide overlay-related operations for future calibration and measurement UI.

## Current Classes

- `DetectionService`: typed adapter around `core.model.DefectDetector`.
- `CaptureService`: creates, switches, and stops image/screen/camera sources.
- `FrameProcessor`: processes one frame with current settings.
- `DefectHistory`: stores recent detections and class counts.
- `OverlayService`: pass-through overlay home for later calibration and measurement drawing.

## Dependencies

Services can depend on `domain`, `core`, and `capture`. They should not depend on UI frameworks.

## Does Not Belong Here

- Dear PyGui widgets.
- Tkinter callbacks.
- Long-running UI loops.
- Training scripts.

