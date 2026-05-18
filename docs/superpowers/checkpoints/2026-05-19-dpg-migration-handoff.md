# DPG Migration Handoff

Date: 2026-05-19

## Workspace

- Worktree: `E:\Code\Horev\wire-detection\.worktrees\dpg-migration`
- Branch: `feat/dpg-migration`
- Latest functional commit before docs: `ca6162f fix: stabilize dpg viewport updates`

## Summary

The DPG migration now has a working backend/service layer and a first Dear PyGui MVP.

Implemented layers:

- `domain/`: typed contracts (`Detection`, `FrameResult`, `ProcessingSettings`, `RuntimeSnapshot`, enums).
- `services/`: capture switching, detection adapter, frame processor, defect history, overlay home.
- `app/`: thin controller, app state, runtime loop, backend factory.
- `ui_dpg/`: DPG app shell, control panel, responsive viewport, defect panel, status bar.

The legacy Tkinter app still exists at `python main.py`. The DPG app starts with `python main_dpg.py`.

## Fixes Since Previous Checkpoint

- Fixed DPG `add_image` parent error during texture recreation.
- Prevented repeated processing of the same cached `FrameResult` in the UI loop.
- Added responsive layout sizing for maximized/fullscreen windows:
  - main DPG window is primary;
  - viewport and defect panels resize from viewport client size;
  - frame texture scales to available viewport panel bounds;
  - defect list resizes with the right panel.

## Verification

Run from the worktree:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/domain tests/services tests/app tests/ui_dpg -q
```

Expected:

```text
30 passed
```

Compile check:

```powershell
..\..\.venv\Scripts\python.exe -m py_compile main_dpg.py ui_dpg/app.py ui_dpg/views/viewport.py ui_dpg/views/defects_panel.py ui_dpg/views/control_panel.py ui_dpg/views/status_bar.py
```

Expected: exit code `0`.

## Manual Smoke Test

```powershell
cd E:\Code\Horev\wire-detection\.worktrees\dpg-migration
..\..\.venv\Scripts\python.exe main_dpg.py
```

Check:

- window opens;
- maximize/fullscreen keeps right panel visible;
- image scales up/down with the viewport;
- `Load Image` works;
- defect list does not duplicate the same static-image result every UI frame;
- `Screen`, `Camera 0`, and `Stop` are usable;
- closing the window stops runtime cleanly.

## Known Remaining Work

- DPG calibration workflow is not migrated yet.
- DPG measurement workflow is not migrated yet.
- Camera selector is still hard-coded to Camera 0 in the MVP.
- Task 7/8 did not receive full separate review gates due to session limit; do a quick code review before merge.
- After manual testing, merge or cherry-pick `feat/dpg-migration` back to `dev`.

## Suggested Next Session

1. Run manual smoke test and note UI/runtime issues.
2. Fix any DPG issues found during manual test.
3. Run tests and compile check.
4. Do a quick review of `ui_dpg/app.py`, `ui_dpg/views/viewport.py`, and `ui_dpg/views/defects_panel.py`.
5. Decide whether to merge `feat/dpg-migration` into `dev`.
