from __future__ import annotations

from datetime import datetime

import dearpygui.dearpygui as dpg


class DefectsPanelView:
    def __init__(self):
        self._rows: list[str] = []

    def build(self) -> None:
        dpg.add_text("Detected Defects")
        dpg.add_text("Total: 0", tag="defects_total")
        dpg.add_text("By Class: none", tag="defects_by_class")
        with dpg.child_window(width=320, height=460, border=True):
            dpg.add_listbox(tag="defects_list", items=[], width=300, num_items=20)

    def update(self, detections, stats) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        for detection in detections:
            self._rows.insert(0, f"[{timestamp}] {detection.class_name} ({detection.confidence:.2f})")
        self._rows = self._rows[:100]
        by_class = ", ".join(f"{name}: {count}" for name, count in stats.by_class.items()) or "none"
        dpg.set_value("defects_total", f"Total: {stats.total}")
        dpg.set_value("defects_by_class", f"By Class: {by_class}")
        dpg.configure_item("defects_list", items=self._rows)
