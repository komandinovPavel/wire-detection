# Codex Development Agreements

This file records the working agreements for future iterations of the wire-detection project.

## Architecture

- Prefer small, focused classes with clear responsibilities.
- Follow SOLID pragmatically, not academically.
- Keep `AppController` thin: it orchestrates use cases but does not contain YOLO, OpenCV, rendering, or business calculations.
- Keep UI layers independent from backend internals.
- Keep backend layers independent from Tkinter, Dear PyGui, or any other UI toolkit.
- Prefer explicit dataclasses/enums for data crossing layer boundaries.
- Favor readable, debuggable flow over clever abstractions.

## UI Direction

- The target UI direction is Dear PyGui.
- The first DPG MVP includes image, screen, and camera sources; YOLO detection; confidence control; defect history; statistics; and status display.
- Calibration and measurement will be added after the first DPG detection MVP.
- Tkinter does not need to remain functional during the refactor, but existing user changes should not be reverted without permission.

## Testing

- Use TDD for core application/service/domain logic where it adds confidence.
- Do not test Dear PyGui widgets in the first phase.
- Do not run real YOLO inference in unit tests.
- Avoid overbuilt fake-object frameworks. Small local stubs are enough when needed.
- Prioritize tests for defect history, frame processing, settings changes, source switching, and error handling.

## Documentation

- Each new major module/layer should have a short Markdown description.
- Module docs should explain purpose, main classes, dependencies, and what does not belong in the module.
- Keep `architecrute.md` or a successor architecture note current when major structure changes.
- Keep this file updated when development agreements change.

## Code Style

- Keep functions and classes easy to read in one sitting.
- Prefer explicit names over compact cleverness.
- Keep comments sparse and useful.
- Avoid large coordinator classes that mix UI, runtime, model inference, and calculations.
- Use structured APIs over ad hoc strings when passing state or results between layers.

