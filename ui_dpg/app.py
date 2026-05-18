from __future__ import annotations

import tkinter as tk
from tkinter import filedialog

import dearpygui.dearpygui as dpg

from app.factory import build_controller
from core.config import Config
from ui_dpg.views.control_panel import ControlPanelView
from ui_dpg.views.defects_panel import DefectsPanelView
from ui_dpg.views.status_bar import StatusBarView
from ui_dpg.views.viewport import ViewportView


class DearPyGuiApp:
    MAIN_WINDOW_TAG = "main_window"
    CONTENT_GROUP_TAG = "content_group"
    VIEWPORT_PANEL_TAG = "viewport_panel"
    DEFECTS_PANEL_TAG = "defects_panel"
    DEFECTS_PANEL_WIDTH = 340
    MIN_DEFECTS_PANEL_WIDTH = 280
    MIN_VIEWPORT_WIDTH = 360
    CONTROL_STATUS_RESERVED_HEIGHT = 120
    PANEL_PADDING = 24

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.controller = build_controller(self.config)
        self.viewport = ViewportView()
        self.defects = DefectsPanelView()
        self.status = StatusBarView()
        self._last_rendered_result = None

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Wire Defect Detector", width=self.config.WINDOW_WIDTH, height=self.config.WINDOW_HEIGHT)
        self._build()
        dpg.setup_dearpygui()
        dpg.set_primary_window(self.MAIN_WINDOW_TAG, True)
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self._update()
            dpg.render_dearpygui_frame()

        self.controller.stop()
        dpg.destroy_context()

    def _build(self) -> None:
        with dpg.window(label="Wire Defect Detector", tag=self.MAIN_WINDOW_TAG, width=self.config.WINDOW_WIDTH, height=self.config.WINDOW_HEIGHT):
            ControlPanelView(
                self.controller,
                self._load_image,
                self.controller.start_screen,
                self.controller.start_camera,
                self.controller.stop,
            ).build()
            with dpg.group(tag=self.CONTENT_GROUP_TAG, horizontal=True):
                with dpg.child_window(tag=self.VIEWPORT_PANEL_TAG, width=980, height=590, border=True):
                    self.viewport.build()
                with dpg.child_window(tag=self.DEFECTS_PANEL_TAG, width=self.DEFECTS_PANEL_WIDTH, height=590, border=True):
                    self.defects.build()
            self.status.build()

    def _load_image(self) -> None:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")],
        )
        root.destroy()
        if path:
            self.controller.load_image(path)

    def _update(self) -> None:
        layout_changed = self._apply_layout()
        result = self.controller.poll_latest_frame()
        if result is not None and result is not self._last_rendered_result:
            self.viewport.update_frame(result.display_frame)
            self.defects.update(result.detections, result.stats)
            self._last_rendered_result = result
        elif result is not None and layout_changed:
            self.viewport.update_frame(result.display_frame)
        self.status.update(self.controller.get_status())

    def _apply_layout(self) -> bool:
        client_width = max(self.config.WINDOW_WIDTH, dpg.get_viewport_client_width())
        client_height = max(self.config.WINDOW_HEIGHT, dpg.get_viewport_client_height())
        content_height = max(260, client_height - self.CONTROL_STATUS_RESERVED_HEIGHT)

        defects_width = self.DEFECTS_PANEL_WIDTH
        if client_width < 900:
            defects_width = self.MIN_DEFECTS_PANEL_WIDTH

        viewport_width = max(
            self.MIN_VIEWPORT_WIDTH,
            client_width - defects_width - self.PANEL_PADDING * 2,
        )

        dpg.configure_item(self.VIEWPORT_PANEL_TAG, width=viewport_width, height=content_height)
        dpg.configure_item(self.DEFECTS_PANEL_TAG, width=defects_width, height=content_height)
        self.defects.resize(defects_width - 20, content_height - 90)
        return self.viewport.set_bounds(
            viewport_width - self.PANEL_PADDING,
            content_height - self.PANEL_PADDING,
        )


def run_app() -> None:
    DearPyGuiApp().run()
