from __future__ import annotations

import dearpygui.dearpygui as dpg


class ControlPanelView:
    def __init__(self, controller, on_load_image, on_start_screen, on_start_camera, on_stop):
        self._controller = controller
        self._on_load_image = on_load_image
        self._on_start_screen = on_start_screen
        self._on_start_camera = on_start_camera
        self._on_stop = on_stop

    def build(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(label="Load Image", callback=lambda: self._on_load_image())
            dpg.add_button(label="Screen", callback=lambda: self._on_start_screen())
            dpg.add_button(label="Camera 0", callback=lambda: self._on_start_camera(0))
            dpg.add_button(label="Stop", callback=lambda: self._on_stop())
            dpg.add_text("Confidence")
            dpg.add_slider_float(
                tag="confidence_slider",
                default_value=0.3,
                min_value=0.1,
                max_value=0.9,
                width=160,
                callback=lambda sender, value: self._controller.set_confidence(value),
            )
