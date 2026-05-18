from __future__ import annotations

import cv2
import numpy as np


def fit_size(source_w: int, source_h: int, max_w: int, max_h: int) -> tuple[int, int]:
    if source_w <= 0 or source_h <= 0:
        return 1, 1
    scale = min(max_w / source_w, max_h / source_h)
    width = max(1, int(source_w * scale))
    height = max(1, int(source_h * scale))
    return width, height


def bgr_frame_to_rgba_float(frame: np.ndarray) -> list[float]:
    rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    return (rgba.astype(float) / 255.0).ravel().tolist()


def resize_for_texture(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
