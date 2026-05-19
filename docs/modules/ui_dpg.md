# UI DPG Module

The `ui_dpg` layer contains the Dear PyGui interface.

## Responsibilities

- Build and update the desktop UI.
- Render frames via DPG textures.
- Display controls, defect history, statistics, and status.
- Call `AppController` for all application actions.

## Current Structure

- `app.py`: creates the DPG context, viewport, main window, native DPG file dialogs, and update loop.
- `views/control_panel.py`: grouped Source and Inspection controls on the left, plus right-aligned Detection, Actions, and standalone Settings controls.
- `views/settings_window.py`: modal DPG settings window for runtime UI settings, including YOLO enable/disable and defect deduplication.
- `views/calibration_window.py`: separate DPG window for calibration image loading, preview, and click-to-calibrate.
- `views/viewport.py`: responsive frame display and texture recreation.
- `views/defects_panel.py`: defect table and class statistics.
- `views/status_bar.py`: badge-style runtime status, active source, mode, YOLO state, measurement state, live FPS, and a compact FPS sparkline.
- `adapters/frame_texture.py`: converts `np.ndarray` frames into DPG texture data.
- `adapters/status_metrics.py`: formats source-aware frame timing/FPS labels and source theme keys.
- `adapters/fps_tracker.py`: tracks live-source FPS from distinct frame arrival intervals and keeps a short history window for the footer sparkline.

## Layout Notes

- `DearPyGuiApp` sets the main window as the primary DPG window.
- The central viewport panel and the right defect panel are resized from viewport client size on every UI tick.
- `ViewportView.set_bounds()` controls the maximum texture size, so images scale when the window is expanded or maximized.
- `ViewportView` can map image clicks back to source-frame coordinates for calibration and measurement.
- `DefectsPanelView.resize()` keeps the defect list usable while the window size changes.
- `ControlPanelView.update()` highlights the selected source from `RuntimeSnapshot.source_type`.
- `SettingsWindowView` is hidden until the user presses `Settings`; runtime tuning controls should live there instead of crowding the toolbar.
- Image and calibration file selection use Dear PyGui file dialogs; the legacy Tkinter UI has been removed.
- `Clear` and `Calibrate` are right-aligned actions; `Settings` is isolated as a compact muted utility control outside the action group.
- The footer includes an explicit bottom safe-area spacer so status badges do not sit flush against the Windows taskbar in fullscreen.
- The source status badge uses source-specific colors; `none` is treated as an error/empty state while active sources remain labeled in text.
- FPS is derived from the interval between distinct live `FrameResult` objects, not from `FrameResult.processing_ms`; this keeps FPS stable when YOLO is disabled and processing time is near zero.
- The FPS sparkline is a small, label-free telemetry graph with a subtle fill; it appears only for live sources after enough samples exist.
- Defect rows are appended from `FrameResult.new_detections`, while the viewport still displays the fully annotated frame.
- When YOLO is disabled in settings, live/image sources still render frames but detection rows and counters do not update.
- `Measure mode` is a toggle in the Inspection group. It is disabled until calibration exists, and source buttons continue to work while it is enabled.

## Dependencies

The DPG UI can depend on `app` and `domain`. It should not depend directly on `core.model`, YOLO, or capture implementations.

## Does Not Belong Here

- Inference logic.
- Frame source lifecycle implementation.
- Defect counting logic.
- Calibration math.
