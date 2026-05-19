from __future__ import annotations

from time import perf_counter

import dearpygui.dearpygui as dpg

from ui_dpg.adapters.fps_tracker import FpsTracker
from ui_dpg.adapters.status_metrics import LIVE_SOURCES, format_frame_badge, source_theme_key, sparkline_points


class StatusBarView:
    STATUS_BADGE = "status_badge"
    SOURCE_BADGE = "source_badge"
    MODE_BADGE = "mode_badge"
    YOLO_BADGE = "yolo_badge"
    MEASURE_BADGE = "measure_badge"
    FRAME_BADGE = "frame_time_badge"
    FPS_GRAPH = "fps_sparkline"
    MESSAGE_TEXT = "status_message_text"
    FPS_GRAPH_WIDTH = 150
    FPS_GRAPH_HEIGHT = 26
    FPS_GRAPH_MAX = 60.0

    BADGE_THEME = "status_badge_theme"
    OK_THEME = "status_ok_badge_theme"
    WARN_THEME = "status_warn_badge_theme"
    ERROR_THEME = "status_error_badge_theme"
    IMAGE_THEME = "status_image_badge_theme"
    SCREEN_THEME = "status_screen_badge_theme"
    CAMERA_THEME = "status_camera_badge_theme"

    def __init__(self) -> None:
        self._fps_tracker = FpsTracker(window_seconds=5.0)

    def build(self) -> None:
        self._build_themes()
        with dpg.group():
            with dpg.group(horizontal=True):
                dpg.add_button(tag=self.STATUS_BADGE, label="Status: ready", width=126, height=24)
                dpg.add_button(tag=self.SOURCE_BADGE, label="Source: none", width=126, height=24)
                dpg.add_button(tag=self.MODE_BADGE, label="Mode: detect", width=118, height=24)
                dpg.add_button(tag=self.YOLO_BADGE, label="YOLO: on", width=100, height=24)
                dpg.add_button(tag=self.MEASURE_BADGE, label="Measure: off", width=120, height=24)
                dpg.add_button(tag=self.FRAME_BADGE, label="Frame: -- ms", width=188, height=24)
                dpg.add_drawlist(tag=self.FPS_GRAPH, width=self.FPS_GRAPH_WIDTH, height=self.FPS_GRAPH_HEIGHT, show=False)
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
        dpg.bind_item_theme(self.SOURCE_BADGE, self.ERROR_THEME)

    def update(self, snapshot, frame_result=None) -> None:
        status = snapshot.status.value
        source_type = snapshot.source_type
        source = source_type.value
        mode = snapshot.mode.value
        yolo_enabled = snapshot.settings.yolo_enabled
        measure_enabled = snapshot.measurement_enabled

        dpg.configure_item(self.STATUS_BADGE, label=f"Status: {status}")
        dpg.configure_item(self.SOURCE_BADGE, label=f"Source: {source}")
        dpg.configure_item(self.MODE_BADGE, label=f"Mode: {mode}")
        dpg.configure_item(self.YOLO_BADGE, label=f"YOLO: {'on' if yolo_enabled else 'off'}")
        dpg.configure_item(self.MEASURE_BADGE, label=f"Measure: {'on' if measure_enabled else 'off'}")

        processing_ms = None if frame_result is None else frame_result.processing_ms
        fps = self._fps_tracker.observe(source_type, frame_result, perf_counter())
        dpg.configure_item(self.FRAME_BADGE, label=format_frame_badge(source_type, processing_ms, fps=fps))
        self._draw_fps_graph(source_type)

        dpg.set_value(self.MESSAGE_TEXT, snapshot.message or "")
        dpg.bind_item_theme(self.STATUS_BADGE, self._theme_for_status(status))
        dpg.bind_item_theme(self.SOURCE_BADGE, self._theme_for_source(source_type))
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

    def _theme_for_source(self, source_type) -> str:
        return {
            "error": self.ERROR_THEME,
            "image": self.IMAGE_THEME,
            "screen": self.SCREEN_THEME,
            "camera": self.CAMERA_THEME,
        }[source_theme_key(source_type)]

    def _draw_fps_graph(self, source_type) -> None:
        dpg.delete_item(self.FPS_GRAPH, children_only=True)
        if source_type not in LIVE_SOURCES or len(self._fps_tracker.samples) < 2:
            dpg.configure_item(self.FPS_GRAPH, show=False)
            return

        dpg.configure_item(self.FPS_GRAPH, show=True)
        fps_values = [sample.fps for sample in self._fps_tracker.samples]
        points = sparkline_points(fps_values, self.FPS_GRAPH_WIDTH, self.FPS_GRAPH_HEIGHT, self.FPS_GRAPH_MAX)
        if not points:
            dpg.configure_item(self.FPS_GRAPH, show=False)
            return

        fill_points = [(0.0, float(self.FPS_GRAPH_HEIGHT)), *points, (float(self.FPS_GRAPH_WIDTH), float(self.FPS_GRAPH_HEIGHT))]
        dpg.draw_polygon(
            fill_points,
            color=(90, 170, 210, 30),
            fill=(90, 170, 210, 24),
            parent=self.FPS_GRAPH,
        )
        dpg.draw_polyline(points, color=(90, 170, 210, 210), thickness=1.5, parent=self.FPS_GRAPH)

    def _build_themes(self) -> None:
        self._build_button_theme(self.BADGE_THEME, (54, 61, 73, 255), (71, 80, 96, 255), (230, 235, 242, 255))
        self._build_button_theme(self.OK_THEME, (35, 105, 68, 255), (42, 128, 82, 255), (236, 255, 244, 255))
        self._build_button_theme(self.WARN_THEME, (128, 96, 36, 255), (150, 112, 42, 255), (255, 246, 220, 255))
        self._build_button_theme(self.ERROR_THEME, (135, 47, 47, 255), (160, 56, 56, 255), (255, 235, 235, 255))
        self._build_button_theme(self.IMAGE_THEME, (36, 88, 140, 255), (45, 108, 170, 255), (235, 245, 255, 255))
        self._build_button_theme(self.SCREEN_THEME, (32, 112, 118, 255), (39, 135, 142, 255), (230, 255, 255, 255))
        self._build_button_theme(self.CAMERA_THEME, (35, 105, 68, 255), (42, 128, 82, 255), (236, 255, 244, 255))

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
