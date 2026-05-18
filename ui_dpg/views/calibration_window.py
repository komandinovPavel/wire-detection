from __future__ import annotations

import dearpygui.dearpygui as dpg

from ui_dpg.views.viewport import ViewportView


class CalibrationWindowView:
    WINDOW_TAG = "calibration_window"
    STATUS_TAG = "calibration_status"
    SCALE_TAG = "calibration_scale"
    RESULT_TAG = "calibration_result"

    def __init__(self, on_load_image, on_calibrate_at):
        self._on_load_image = on_load_image
        self._on_calibrate_at = on_calibrate_at
        self.viewport = ViewportView(
            texture_tag="calibration_texture",
            image_tag="calibration_image",
            texture_registry_tag="calibration_texture_registry",
            container_tag="calibration_image_container",
            handler_registry_tag="calibration_image_handlers",
        )
        self.viewport.set_on_click(lambda x, y: self._on_calibrate_at(x))

    def build(self) -> None:
        with dpg.window(
            label="Calibration",
            tag=self.WINDOW_TAG,
            width=960,
            height=680,
            show=False,
            no_resize=False,
        ):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Load image", width=120, height=34, callback=lambda: self._on_load_image())
                dpg.add_button(label="Close", width=90, height=34, callback=lambda: self.hide())
            dpg.add_text("Status: load a calibration image, then click on the wire", tag=self.STATUS_TAG)
            dpg.add_text("Scale: not calibrated", tag=self.SCALE_TAG)
            dpg.add_text("Result: none", tag=self.RESULT_TAG)
            with dpg.child_window(width=-1, height=520, border=True):
                self.viewport.build()

    def show(self) -> None:
        dpg.configure_item(self.WINDOW_TAG, show=True)

    def hide(self) -> None:
        dpg.configure_item(self.WINDOW_TAG, show=False)

    def update_frame(self, frame) -> None:
        self.viewport.update_frame(frame)

    def update_loaded(self) -> None:
        dpg.set_value(self.STATUS_TAG, "Status: click on the wire to calibrate")
        dpg.set_value(self.RESULT_TAG, "Result: waiting for click")

    def update_result(self, result) -> None:
        dpg.set_value(self.STATUS_TAG, "Status: calibrated")
        dpg.set_value(self.SCALE_TAG, f"Scale: {result.pixels_per_mm:.3f} px/mm")
        dpg.set_value(
            self.RESULT_TAG,
            f"Measured: {result.measured_diameter_mm:.3f} mm | Deviation: {result.deviation_mm:+.3f} mm",
        )
