# Services Module

The `services` layer contains backend use cases and reusable application logic.

## Responsibilities

- Process frames.
- Run detection through a model adapter.
- Manage capture source selection.
- Track defect history and statistics.
- Turn repeated live-frame detections into deduplicated defect events.
- Calibrate pixel scale and measure wire diameter on still frames.
- Draw measurement/calibration overlays for UI display.

## Current Classes

- `DetectionService`: typed adapter around `core.model.DefectDetector`.
- `CaptureService`: creates, switches, stops, and probes image/screen/camera sources.
- `FrameProcessor`: processes one frame with current settings and adds only new defect events to history.
- `DefectEventFilter`: deduplicates stable live detections by class, bbox IoU, and time window.
- `CalibrationService`: computes `px/mm` from a clicked wire point and measures diameter after calibration.
- `MeasurementOverlay`: draws calibration and measurement infographics on BGR frames.
- `DefectHistory`: stores recent detections and class counts.
- `OverlayService`: pass-through overlay home for later calibration and measurement drawing.

## Detection Event Semantics

- `FrameResult.detections` means all detections visible in the current processed frame.
- `FrameResult.new_detections` means detections that should increment history/statistics.
- `ProcessingSettings.deduplicate_defects` controls whether `FrameProcessor` applies `DefectEventFilter` or counts every current detection as a new event.
- `ProcessingSettings.yolo_enabled` controls whether `FrameProcessor` calls the detector at all. When disabled, the source frame passes through unchanged and no new detections are counted.
- The UI can still render all current detections while counters avoid per-frame spam from one stable defect.

## Calibration Semantics

- Calibration uses `WireAnalyzer.measure_diameter_at_x(image, x)` at the clicked wire coordinate.
- `pixels_per_mm = calibration_diameter_px / nominal_diameter_mm`.
- Measurement mode uses a frozen clean frame, not the YOLO-annotated display frame.
- Overlay rendering stays in services so DPG widgets do not contain OpenCV drawing logic.

## Dependencies

Services can depend on `domain`, `core`, and `capture`. They should not depend on UI frameworks.

## Does Not Belong Here

- Dear PyGui widgets.
- Tkinter callbacks.
- Long-running UI loops.
- Training scripts.

