from __future__ import annotations

import dearpygui.dearpygui as dpg


class SettingsWindowView:
    WINDOW_TAG = "settings_window"
    DEDUP_CHECKBOX = "deduplication_checkbox"

    def __init__(self, controller):
        self._controller = controller

    def build(self) -> None:
        settings = self._controller.get_status().settings
        with dpg.window(
            label="Settings",
            tag=self.WINDOW_TAG,
            width=360,
            height=140,
            modal=True,
            show=False,
            no_resize=True,
        ):
            dpg.add_text("Defect detection")
            dpg.add_checkbox(
                tag=self.DEDUP_CHECKBOX,
                label="Deduplicate same defects",
                default_value=settings.deduplicate_defects,
                callback=lambda sender, value: self._controller.set_deduplication_enabled(value),
            )
            dpg.add_button(label="Close", width=100, height=32, callback=lambda: self.hide())

    def show(self) -> None:
        dpg.configure_item(self.WINDOW_TAG, show=True)

    def hide(self) -> None:
        dpg.configure_item(self.WINDOW_TAG, show=False)

    def update(self, snapshot) -> None:
        dpg.set_value(self.DEDUP_CHECKBOX, snapshot.settings.deduplicate_defects)
