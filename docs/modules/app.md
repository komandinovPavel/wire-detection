# App Module

The `app` layer contains application use-case orchestration. It sits between UI code and backend services.

## Responsibilities

- Expose a thin `AppController` API for UI commands.
- Manage runtime state and background processing.
- Provide snapshots/results for UI polling.
- Keep UI code away from YOLO, OpenCV capture sources, and defect-counting internals.

## Planned Classes

- `AppController`: command facade for UI.
- `ProcessingRuntime`: background loop for camera and screen processing.
- `AppState`: current settings, selected source, mode, and status.
- `events` / DTOs: simple event or snapshot objects for UI consumption.

## Dependencies

The app layer can depend on `domain` and `services`. It should not depend on Dear PyGui or Tkinter.

## Does Not Belong Here

- Widget creation.
- YOLO inference implementation.
- OpenCV drawing details.
- Calibration math.

