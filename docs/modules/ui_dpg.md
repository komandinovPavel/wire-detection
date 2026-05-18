# UI DPG Module

The `ui_dpg` layer contains the Dear PyGui interface.

## Responsibilities

- Build and update the desktop UI.
- Render frames via DPG textures.
- Display controls, defect history, statistics, and status.
- Call `AppController` for all application actions.

## Planned Structure

- `app.py`: creates the DPG context, viewport, main window, and update loop.
- `views/control_panel.py`: source buttons and confidence slider.
- `views/viewport.py`: frame display.
- `views/defects_panel.py`: defect table and class statistics.
- `views/status_bar.py`: runtime status.
- `adapters/frame_texture.py`: converts `np.ndarray` frames into DPG texture data.
- `adapters/file_dialogs.py`: file selection helpers if needed.

## Dependencies

The DPG UI can depend on `app` and `domain`. It should not depend directly on `core.model`, YOLO, or capture implementations.

## Does Not Belong Here

- Inference logic.
- Frame source lifecycle implementation.
- Defect counting logic.
- Calibration math.

