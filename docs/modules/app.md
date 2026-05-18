# App Module

The `app` layer contains application use-case orchestration. It sits between UI code and backend services.

## Responsibilities

- Expose a thin `AppController` API for UI commands.
- Manage runtime state and background processing.
- Provide snapshots/results for UI polling.
- Provide UI-safe commands for camera discovery, runtime setting changes, and defect history clearing.
- Expose calibration and measurement commands while keeping OpenCV math in services.
- Keep UI code away from YOLO, OpenCV capture sources, and defect-counting internals.

## Current Classes

- `AppController`: command facade for UI, including source start/stop, camera listing, settings, and defect clearing.
- `ProcessingRuntime`: background loop for camera and screen processing.
- `AppState`: current settings, selected source, mode, and status.
- `build_controller()`: composition root that wires config, detector, services, runtime, and controller.

## Runtime Notes

- `ProcessingRuntime.run_once()` is the testable one-frame path.
- `ProcessingRuntime.start()` stops the old worker before starting a new one.
- If a previous worker does not stop inside its timeout, runtime raises `RuntimeError` instead of hiding a still-live thread.
- `AppController.start_camera()` and `start_screen()` convert source startup failures into `RuntimeStatus.ERROR` snapshots instead of letting UI callbacks crash.
- `AppController.set_deduplication_enabled()` updates `ProcessingSettings` while preserving confidence and image size.
- `AppController.load_calibration_image()` loads a clean calibration frame without running YOLO.
- `AppController.start_measurement_mode()` freezes the latest clean frame so clicks measure the image the user sees.

## Dependencies

The app layer can depend on `domain` and `services`. It should not depend on Dear PyGui or Tkinter.

## Does Not Belong Here

- Widget creation.
- YOLO inference implementation.
- OpenCV drawing details.
- Calibration math.

