# UI DPG Module

The `ui_dpg` layer contains the Dear PyGui interface.

## Responsibilities

- Build and update the desktop UI.
- Render frames via DPG textures.
- Display controls, defect history, statistics, and status.
- Call `AppController` for all application actions.

## Current Structure

- `app.py`: creates the DPG context, viewport, main window, and update loop.
- `views/control_panel.py`: source buttons, camera button, camera list combo, active-source styling, stop styling, settings action, clear action, and confidence slider.
- `views/settings_window.py`: modal DPG settings window for runtime UI settings.
- `views/viewport.py`: responsive frame display and texture recreation.
- `views/defects_panel.py`: defect table and class statistics.
- `views/status_bar.py`: runtime status, active source, and latest frame processing time.
- `adapters/frame_texture.py`: converts `np.ndarray` frames into DPG texture data.

## Layout Notes

- `DearPyGuiApp` sets the main window as the primary DPG window.
- The central viewport panel and the right defect panel are resized from viewport client size on every UI tick.
- `ViewportView.set_bounds()` controls the maximum texture size, so images scale when the window is expanded or maximized.
- `DefectsPanelView.resize()` keeps the defect list usable while the window size changes.
- `ControlPanelView.update()` highlights the selected source from `RuntimeSnapshot.source_type`.
- `SettingsWindowView` is hidden until the user presses `Settings`; runtime tuning controls should live there instead of crowding the toolbar.
- Defect rows are appended from `FrameResult.new_detections`, while the viewport still displays the fully annotated frame.

## Dependencies

The DPG UI can depend on `app` and `domain`. It should not depend directly on `core.model`, YOLO, or capture implementations.

## Does Not Belong Here

- Inference logic.
- Frame source lifecycle implementation.
- Defect counting logic.
- Calibration math.

