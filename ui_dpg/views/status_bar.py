from __future__ import annotations

import dearpygui.dearpygui as dpg


class StatusBarView:
    def build(self) -> None:
        dpg.add_text("Status: Ready", tag="status_text")

    def update(self, snapshot) -> None:
        text = f"Status: {snapshot.status.value} | {snapshot.message}"
        dpg.set_value("status_text", text)
