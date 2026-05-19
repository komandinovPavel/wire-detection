from __future__ import annotations

import math

from domain import SourceType


LIVE_SOURCES = {SourceType.CAMERA, SourceType.SCREEN}


def format_frame_badge(source_type: SourceType, processing_ms: float | None) -> str:
    if processing_ms is None:
        return "Frame: -- ms"
    if not math.isfinite(processing_ms):
        return "Frame: -- ms"

    label = f"Frame: {processing_ms:.1f} ms"
    if source_type in LIVE_SOURCES and processing_ms > 0:
        label = f"{label} / {1000.0 / processing_ms:.1f} FPS"
    return label


def source_theme_key(source_type: SourceType) -> str:
    if source_type is SourceType.NONE:
        return "error"
    return source_type.value
