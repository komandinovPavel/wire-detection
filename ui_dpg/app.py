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
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self._update()
            dpg.render_dearpygui_frame()

        self.controller.stop()
        dpg.destroy_context()

    def _build(self) -> None:
        with dpg.window(label="Wire Defect Detector", tag="main_window", width=self.config.WINDOW_WIDTH, height=self.config.WINDOW_HEIGHT):
            ControlPanelView(
                self.controller,
                self._load_image,
                self.controller.start_screen,
                self.controller.start_camera,
                self.controller.stop,
            ).build()
            with dpg.group(horizontal=True):
                with dpg.child_window(width=980, height=590, border=True):
                    self.viewport.build()
                with dpg.child_window(width=340, height=590, border=True):
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
        result = self.controller.poll_latest_frame()
        if result is not None and result is not self._last_rendered_result:
            self.viewport.update_frame(result.display_frame)
            self.defects.update(result.detections, result.stats)
            self._last_rendered_result = result
        self.status.update(self.controller.get_status())


def run_app() -> None:
    DearPyGuiApp().run()
