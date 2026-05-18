from __future__ import annotations

import dearpygui.dearpygui as dpg


class StatusBarView:
    def build(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_text("Status: Ready", tag="status_text")
            dpg.add_text("Source: none", tag="source_text")
            dpg.add_text("Frame: -- ms", tag="frame_time_text")

    def update(self, snapshot, frame_result=None) -> None:
        dpg.set_value("status_text", f"Status: {snapshot.status.value} | {snapshot.message}")
        dpg.set_value("source_text", f"Source: {snapshot.source_type.value}")
        if frame_result is None:
            dpg.set_value("frame_time_text", "Frame: -- ms")
        else:
            dpg.set_value("frame_time_text", f"Frame: {frame_result.processing_ms:.1f} ms")
