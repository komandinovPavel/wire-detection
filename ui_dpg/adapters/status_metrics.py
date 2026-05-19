from __future__ import annotations

import math

from domain import SourceType


LIVE_SOURCES = {SourceType.CAMERA, SourceType.SCREEN}


def format_frame_badge(source_type: SourceType, processing_ms: float | None, fps: float | None = None) -> str:
    if processing_ms is None:
        return "Frame: -- ms"
    if not math.isfinite(processing_ms):
        return "Frame: -- ms"

    label = f"Frame: {processing_ms:.1f} ms"
    if source_type in LIVE_SOURCES:
        fps_label = f"{fps:.1f}" if fps is not None and math.isfinite(fps) and fps > 0 else "--"
        label = f"{label} / {fps_label} FPS"
    return label


def source_theme_key(source_type: SourceType) -> str:
    if source_type is SourceType.NONE:
        return "error"
    return source_type.value


def sparkline_points(fps_values: list[float], width: int, height: int, max_fps: float = 60.0) -> list[tuple[float, float]]:
    if len(fps_values) < 2:
        return []

    step = float(width) / float(len(fps_values) - 1)
    points = []
    for index, fps in enumerate(fps_values):
        clamped = min(max(float(fps), 0.0), max_fps)
        x = index * step
        y = float(height) - (clamped / max_fps * float(height))
        points.append((round(x, 3), round(y, 3)))
    return points
