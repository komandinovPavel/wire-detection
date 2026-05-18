from __future__ import annotations

import dearpygui.dearpygui as dpg


class ControlPanelView:
    IMAGE_BUTTON = "source_image_button"
    SCREEN_BUTTON = "source_screen_button"
    CAMERA_BUTTON = "source_camera_button"
    MEASURE_BUTTON = "measure_button"
    MEASURE_HINT = "measure_hint"
    REFRESH_BUTTON = "refresh_cameras_button"
    STOP_BUTTON = "stop_button"
    CLEAR_BUTTON = "clear_defects_button"
    CALIBRATE_BUTTON = "calibrate_button"
    SETTINGS_BUTTON = "settings_button"
    CAMERA_COMBO = "camera_combo"
    NORMAL_THEME = "normal_button_theme"
    ACTIVE_SOURCE_THEME = "active_source_theme"
    STOP_THEME = "stop_button_theme"

    def __init__(
        self,
        controller,
        on_load_image,
        on_start_screen,
        on_start_camera,
        on_stop,
        on_clear_defects,
        on_open_settings,
        on_open_calibration,
        on_measurement_toggle,
    ):
        self._controller = controller
        self._on_load_image = on_load_image
        self._on_start_screen = on_start_screen
        self._on_start_camera = on_start_camera
        self._on_stop = on_stop
        self._on_clear_defects = on_clear_defects
        self._on_open_settings = on_open_settings
        self._on_open_calibration = on_open_calibration
        self._on_measurement_toggle = on_measurement_toggle

    def build(self) -> None:
        self._build_themes()
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text("Source")
                with dpg.group(horizontal=True):
                    dpg.add_button(tag=self.IMAGE_BUTTON, label="Image", width=96, height=34, callback=lambda: self._on_load_image())
                    dpg.add_button(tag=self.SCREEN_BUTTON, label="Screen", width=96, height=34, callback=lambda: self._on_start_screen())
                    dpg.add_button(tag=self.CAMERA_BUTTON, label="Camera", width=96, height=34, callback=lambda: self._start_selected_camera())
                    dpg.add_button(tag=self.STOP_BUTTON, label="Stop capture", width=112, height=34, callback=lambda: self._on_stop())
                with dpg.group(horizontal=True):
                    dpg.add_text("Camera list")
                    dpg.add_combo(tag=self.CAMERA_COMBO, items=["0"], default_value="0", width=90)
                    dpg.add_button(tag=self.REFRESH_BUTTON, label="R", width=28, height=24, callback=lambda: self.refresh_cameras())
            dpg.add_spacer(width=12)
            with dpg.group():
                dpg.add_text("Inspection")
                dpg.add_checkbox(tag=self.MEASURE_BUTTON, label="Measure mode", callback=lambda sender, value: self._on_measurement_toggle(value))
                dpg.add_text("Calibrate first", tag=self.MEASURE_HINT)
            dpg.add_spacer(width=12)
            with dpg.group():
                dpg.add_text("Tools")
                with dpg.group(horizontal=True):
                    dpg.add_button(tag=self.CALIBRATE_BUTTON, label="Calibrate", width=112, height=34, callback=lambda: self._on_open_calibration())
                    dpg.add_button(tag=self.CLEAR_BUTTON, label="Clear", width=100, height=34, callback=lambda: self._on_clear_defects())
                    dpg.add_button(tag=self.SETTINGS_BUTTON, label="Settings", width=112, height=34, callback=lambda: self._on_open_settings())
                with dpg.group(horizontal=True):
                    dpg.add_text("Confidence")
                    dpg.add_slider_float(
                        tag="confidence_slider",
                        default_value=0.3,
                        min_value=0.1,
                        max_value=0.9,
                        width=180,
                        callback=lambda sender, value: self._controller.set_confidence(value),
                    )
        dpg.bind_item_theme(self.STOP_BUTTON, self.STOP_THEME)

    def refresh_cameras(self) -> None:
        cameras = [str(index) for index in self._controller.list_cameras()]
        dpg.configure_item(self.CAMERA_COMBO, items=cameras)
        dpg.set_value(self.CAMERA_COMBO, cameras[0])

    def update(self, snapshot) -> None:
        active_tag = {
            "image": self.IMAGE_BUTTON,
            "screen": self.SCREEN_BUTTON,
            "camera": self.CAMERA_BUTTON,
        }.get(snapshot.source_type.value)
        for tag in [self.IMAGE_BUTTON, self.SCREEN_BUTTON, self.CAMERA_BUTTON]:
            theme = self.ACTIVE_SOURCE_THEME if tag == active_tag else self.NORMAL_THEME
            dpg.bind_item_theme(tag, theme)
        dpg.bind_item_theme(self.STOP_BUTTON, self.STOP_THEME)
        dpg.set_value(self.MEASURE_BUTTON, snapshot.measurement_enabled)
        can_measure = self._controller.is_calibrated()
        dpg.configure_item(self.MEASURE_BUTTON, enabled=can_measure)
        dpg.configure_item(self.MEASURE_HINT, show=not can_measure)

    def _start_selected_camera(self) -> None:
        value = dpg.get_value(self.CAMERA_COMBO) or "0"
        self._on_start_camera(int(value))

    def _build_themes(self) -> None:
        with dpg.theme(tag=self.NORMAL_THEME):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (65, 72, 86, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (79, 88, 105, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (92, 102, 122, 255))

        with dpg.theme(tag=self.ACTIVE_SOURCE_THEME):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (35, 125, 74, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (42, 150, 89, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (29, 100, 60, 255))

        with dpg.theme(tag=self.STOP_THEME):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (150, 48, 48, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (180, 58, 58, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (125, 39, 39, 255))
