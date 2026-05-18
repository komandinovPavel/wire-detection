# DPG Migration Design

Date: 2026-05-18

## Goal

Move the project toward a Dear PyGui desktop application without losing the current detection workflow. The first implementation phase focuses on backend separation and a DPG MVP for image, screen, and camera sources with YOLO detection, confidence control, defect history, and status reporting.

Calibration and measurement remain important project capabilities, but they are not part of the first DPG UI milestone. The design keeps space for them as separate services so they can be added later without reshaping the whole application.

## Decisions

- Use a service-oriented architecture around use cases.
- Do not preserve Tkinter as a required working UI during the refactor.
- Keep `AppController` thin and readable.
- Follow SOLID pragmatically: small classes, clear dependencies, and one main reason for change per class.
- Keep backend independent from DPG and Tkinter.
- Use TDD for core/application/service classes, but avoid heavy fake-object frameworks and UI tests.
- Add short module documentation for every new major layer.
- Add `codex.md` with development agreements for future work.

## Target Structure

```text
main_dpg.py

ui_dpg/
  app.py
  views/
    control_panel.py
    viewport.py
    defects_panel.py
    status_bar.py
  adapters/
    frame_texture.py
    file_dialogs.py

app/
  controller.py
  runtime.py
  state.py
  events.py

domain/
  models.py
  enums.py

services/
  detection_service.py
  capture_service.py
  defect_history.py
  frame_processor.py
  overlay_service.py

core/
  model.py
  wire_analyzer.py
  calibration.py
  config.py

capture/
  base.py
  image.py
  screen.py
  camera.py
```

## Component Responsibilities

### UI Layer

`ui_dpg` owns Dear PyGui widgets and rendering. It should only call `AppController`, poll frame results, update textures, update controls, and show status. It must not call YOLO, OpenCV capture sources, or measurement logic directly.

The first DPG screen contains:

- source controls: load image, start screen capture, start camera, stop;
- confidence slider;
- central frame viewport;
- defect table/history;
- class statistics;
- status area.

### App Layer

`AppController` is the facade used by UI code. It accepts user commands and exposes snapshots/results:

- `load_image(path)`;
- `start_camera(index)`;
- `start_screen()`;
- `stop()`;
- `set_confidence(value)`;
- `poll_latest_frame()`;
- `get_defects_snapshot()`;
- `get_status()`.

The controller delegates to runtime and services. It does not perform inference, frame drawing, capture reads, or defect counting internally.

`ProcessingRuntime` owns the background loop for camera and screen capture. It reads frames, calls `FrameProcessor`, stores the latest result, and keeps the latest runtime error/status. DPG reads results from the main UI loop by polling the controller.

### Domain Layer

`domain` contains small dataclasses and enums. These models are stable contracts between services and UI:

- `Detection`;
- `FrameResult`;
- `ProcessingSettings`;
- `DefectStats`;
- `RuntimeSnapshot`;
- `SourceType`;
- `AppMode`;
- `RuntimeStatus`.

### Services Layer

`DetectionService` adapts `core.model.DefectDetector` into typed domain results. It normalizes YOLO output and handles model/inference errors without exposing YOLO internals to UI.

`CaptureService` creates and switches frame sources. It knows about `ImageCapture`, `ScreenCapture`, and `CameraCapture`. It stops the previous source before starting a new one.

`FrameProcessor` handles the use case "process one frame". It receives a clean `np.ndarray` and settings, calls `DetectionService`, updates `DefectHistory`, and returns `FrameResult`.

`DefectHistory` stores the last N detections, total counts, and class statistics. This is a key unit-test target.

`OverlayService` is reserved for visual overlays. The first MVP can rely on `DefectDetector` annotated frames, but calibration and measurement overlays should move here later.

### Core and Capture Layers

Existing `core` and `capture` modules remain low-level implementation layers. They should be adjusted only as needed to expose clean APIs. `WireAnalyzer` and calibration logic should not be mixed into DPG widgets.

## Data Flow

### Static Image

```text
DPG UI
  -> AppController.load_image(path)
  -> CaptureService.load_image(path)
  -> FrameProcessor.process(frame, settings)
  -> DetectionService.detect(frame, settings)
  -> DefectHistory.add(detections)
  -> FrameResult
  -> DPG updates texture/table/status
```

This path is synchronous because it processes a single selected image.

### Camera and Screen

```text
DPG UI
  -> AppController.start_camera(index) or start_screen()
  -> CaptureService.start(...)
  -> ProcessingRuntime.start()

background loop:
  CaptureSource.read_frame()
  -> FrameProcessor.process(frame, settings)
  -> latest FrameResult cache

DPG UI loop:
  -> AppController.poll_latest_frame()
  -> update texture/table/status
```

The UI thread never receives direct callbacks from the background loop. Polling keeps the interaction simple and debuggable.

## Error Handling

Runtime state should be explicit:

```text
IDLE
LOADING_MODEL
READY
RUNNING
STOPPED
ERROR
```

Expected behaviors:

- If a camera cannot open, set `ERROR` and keep the UI responsive.
- If the model is missing, detection returns no detections and a clear error status.
- If a source returns `None`, skip or report the frame without crashing runtime.
- If inference raises, return an error `FrameResult`; the runtime can continue unless the source itself is stopped.
- Prefer structured result objects over scattered `print()` calls.

## Testing Strategy

Use targeted tests for working core/application/service classes.

Initial test targets:

- `DefectHistory` counts total detections, class statistics, and limits history size.
- `FrameProcessor` returns a successful `FrameResult` when detection succeeds.
- `FrameProcessor` returns an error result when detection fails.
- `AppController` updates settings and delegates source commands.
- `CaptureService` switches sources and stops the previous source.

Not in first test scope:

- real YOLO inference;
- Dear PyGui widgets;
- real camera/screen capture;
- pixel-perfect overlay rendering.

The tests may use small in-memory stubs where useful, but should avoid complex fake-object frameworks.

## Documentation

Add and maintain:

- `codex.md` for project development agreements;
- `docs/modules/app.md`;
- `docs/modules/services.md`;
- `docs/modules/domain.md`;
- `docs/modules/ui_dpg.md`.

Each module document should stay short and answer:

- what the layer does;
- what the main classes are;
- what the layer depends on;
- what should not be placed there.

## Migration Plan

1. Add domain models and service skeletons with focused tests.
2. Move frame-processing behavior out of `ui/main_window.py` into services.
3. Introduce `AppController` and `ProcessingRuntime`.
4. Build `main_dpg.py` and `ui_dpg` MVP for image, screen, camera, YOLO, confidence, status, and defect history.
5. Run the DPG MVP against the existing model and sample images.
6. Decide whether to keep Tkinter as legacy fallback or remove it.
7. Add calibration and measurement workflows through dedicated services and overlays.

## Non-Goals for First DPG MVP

- Reworking YOLO training scripts.
- Rewriting calibration and measurement UI.
- Supporting remote web clients.
- Packaging as an executable installer.
- Pixel-perfect visual polish.

