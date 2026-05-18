from __future__ import annotations

import dearpygui.dearpygui as dpg

from ui_dpg.adapters.frame_texture import bgr_frame_to_rgba_float, fit_size, resize_for_texture


class ViewportView:
    def __init__(
        self,
        texture_tag: str = "frame_texture",
        image_tag: str = "frame_image",
        texture_registry_tag: str = "frame_texture_registry",
        container_tag: str = "frame_image_container",
    ):
        self.texture_tag = texture_tag
        self.image_tag = image_tag
        self.texture_registry_tag = texture_registry_tag
        self.container_tag = container_tag
        self._width = 640
        self._height = 360
        self._max_width = 960
        self._max_height = 540

    def build(self) -> None:
        with dpg.texture_registry(tag=self.texture_registry_tag):
            dpg.add_dynamic_texture(self._width, self._height, [0.0] * self._width * self._height * 4, tag=self.texture_tag)
        with dpg.group(tag=self.container_tag):
            dpg.add_image(self.texture_tag, tag=self.image_tag)

    def set_bounds(self, max_width: int, max_height: int) -> bool:
        max_width = max(1, int(max_width))
        max_height = max(1, int(max_height))
        changed = max_width != self._max_width or max_height != self._max_height
        self._max_width = max_width
        self._max_height = max_height
        return changed

    def update_frame(self, frame) -> None:
        if frame is None:
            return
        height, width = frame.shape[:2]
        new_width, new_height = fit_size(width, height, self._max_width, self._max_height)
        resized = resize_for_texture(frame, new_width, new_height)
        data = bgr_frame_to_rgba_float(resized)

        if new_width != self._width or new_height != self._height:
            self._width = new_width
            self._height = new_height
            if dpg.does_item_exist(self.image_tag):
                dpg.delete_item(self.image_tag)
            if dpg.does_item_exist(self.texture_tag):
                dpg.delete_item(self.texture_tag)
            dpg.add_dynamic_texture(self._width, self._height, data, tag=self.texture_tag, parent=self.texture_registry_tag)
            dpg.add_image(self.texture_tag, tag=self.image_tag, parent=self.container_tag)
        else:
            dpg.set_value(self.texture_tag, data)
