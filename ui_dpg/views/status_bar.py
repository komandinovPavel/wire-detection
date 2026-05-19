from __future__ import annotations

import dearpygui.dearpygui as dpg


class StatusBarView:
    STATUS_BADGE = "status_badge"
    SOURCE_BADGE = "source_badge"
    MODE_BADGE = "mode_badge"
    YOLO_BADGE = "yolo_badge"
    MEASURE_BADGE = "measure_badge"
    FRAME_BADGE = "frame_time_badge"
    MESSAGE_TEXT = "status_message_text"

    BADGE_THEME = "status_badge_theme"
    OK_THEME = "status_ok_badge_theme"
    WARN_THEME = "status_warn_badge_theme"
    ERROR_THEME = "status_error_badge_theme"

    def build(self) -> None:
        self._build_themes()
        with dpg.group():
            with dpg.group(horizontal=True):
                dpg.add_button(tag=self.STATUS_BADGE, label="Status: ready", width=126, height=24)
                dpg.add_button(tag=self.SOURCE_BADGE, label="Source: none", width=126, height=24)
                dpg.add_button(tag=self.MODE_BADGE, label="Mode: detect", width=118, height=24)
                dpg.add_button(tag=self.YOLO_BADGE, label="YOLO: on", width=100, height=24)
                dpg.add_button(tag=self.MEASURE_BADGE, label="Measure: off", width=120, height=24)
                dpg.add_button(tag=self.FRAME_BADGE, label="Frame: -- ms", width=116, height=24)
            dpg.add_text("", tag=self.MESSAGE_TEXT)
        for tag in [
            self.STATUS_BADGE,
            self.SOURCE_BADGE,
            self.MODE_BADGE,
            self.MEASURE_BADGE,
            self.FRAME_BADGE,
        ]:
            dpg.bind_item_theme(tag, self.BADGE_THEME)
        dpg.bind_item_theme(self.YOLO_BADGE, self.OK_THEME)

    def update(self, snapshot, frame_result=None) -> None:
        status = snapshot.status.value
        source = snapshot.source_type.value
        mode = snapshot.mode.value
        yolo_enabled = snapshot.settings.yolo_enabled
        measure_enabled = snapshot.measurement_enabled

        dpg.configure_item(self.STATUS_BADGE, label=f"Status: {status}")
        dpg.configure_item(self.SOURCE_BADGE, label=f"Source: {source}")
        dpg.configure_item(self.MODE_BADGE, label=f"Mode: {mode}")
        dpg.configure_item(self.YOLO_BADGE, label=f"YOLO: {'on' if yolo_enabled else 'off'}")
        dpg.configure_item(self.MEASURE_BADGE, label=f"Measure: {'on' if measure_enabled else 'off'}")

        if frame_result is None:
            dpg.configure_item(self.FRAME_BADGE, label="Frame: -- ms")
        else:
            dpg.configure_item(self.FRAME_BADGE, label=f"Frame: {frame_result.processing_ms:.1f} ms")

        dpg.set_value(self.MESSAGE_TEXT, snapshot.message or "")
        dpg.bind_item_theme(self.STATUS_BADGE, self._theme_for_status(status))
        dpg.bind_item_theme(self.YOLO_BADGE, self.OK_THEME if yolo_enabled else self.WARN_THEME)
        dpg.bind_item_theme(self.MEASURE_BADGE, self.OK_THEME if measure_enabled else self.BADGE_THEME)

    def _theme_for_status(self, status: str) -> str:
        if status in {"running", "ready"}:
            return self.OK_THEME
        if status == "error":
            return self.ERROR_THEME
        if status == "stopped":
            return self.WARN_THEME
        return self.BADGE_THEME

    def _build_themes(self) -> None:
        self._build_button_theme(self.BADGE_THEME, (54, 61, 73, 255), (71, 80, 96, 255), (230, 235, 242, 255))
        self._build_button_theme(self.OK_THEME, (35, 105, 68, 255), (42, 128, 82, 255), (236, 255, 244, 255))
        self._build_button_theme(self.WARN_THEME, (128, 96, 36, 255), (150, 112, 42, 255), (255, 246, 220, 255))
        self._build_button_theme(self.ERROR_THEME, (135, 47, 47, 255), (160, 56, 56, 255), (255, 235, 235, 255))

    def _build_button_theme(
        self,
        tag: str,
        color: tuple[int, int, int, int],
        hovered: tuple[int, int, int, int],
        text: tuple[int, int, int, int],
    ) -> None:
        with dpg.theme(tag=tag):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hovered)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, color)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text)
