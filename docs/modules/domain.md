# Domain Module

The `domain` layer contains small shared types used across app, services, and UI.

## Responsibilities

- Define stable data contracts.
- Keep state and result objects explicit.
- Avoid framework dependencies.

## Planned Types

- `Detection`
- `FrameResult`
- `ProcessingSettings`
- `DefectStats`
- `RuntimeSnapshot`
- `SourceType`
- `AppMode`
- `RuntimeStatus`

## Dependencies

The domain layer should depend only on Python standard library types and lightweight typing/dataclass features.

## Does Not Belong Here

- YOLO objects.
- OpenCV capture handles.
- Dear PyGui texture IDs.
- Tkinter widgets.
- Business processes or runtime loops.

