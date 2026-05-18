from __future__ import annotations

from datetime import datetime

import dearpygui.dearpygui as dpg


class DefectsPanelView:
    def __init__(self, list_container_tag: str = "defects_list_container"):
        self._rows: list[str] = []
        self.list_container_tag = list_container_tag

    def build(self) -> None:
        dpg.add_text("Detected Defects")
        dpg.add_text("Total: 0", tag="defects_total")
        dpg.add_text("By Class: none", tag="defects_by_class")
        with dpg.child_window(tag=self.list_container_tag, width=320, height=460, border=True):
            dpg.add_listbox(tag="defects_list", items=[], width=300, num_items=20)

    def resize(self, width: int, height: int) -> None:
        width = max(220, int(width))
        height = max(180, int(height))
        dpg.configure_item(self.list_container_tag, width=width, height=height)
        dpg.configure_item(
            "defects_list",
            width=max(180, width - 20),
            num_items=max(6, min(30, height // 24)),
        )

    def clear(self) -> None:
        self._rows.clear()
        dpg.set_value("defects_total", "Total: 0")
        dpg.set_value("defects_by_class", "By Class: none")
        dpg.configure_item("defects_list", items=[])

    def update(self, detections, stats) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        for detection in detections:
            self._rows.insert(0, f"[{timestamp}] {detection.class_name} ({detection.confidence:.2f})")
        self._rows = self._rows[:100]
        by_class = ", ".join(f"{name}: {count}" for name, count in stats.by_class.items()) or "none"
        dpg.set_value("defects_total", f"Total: {stats.total}")
        dpg.set_value("defects_by_class", f"By Class: {by_class}")
        dpg.configure_item("defects_list", items=self._rows)
