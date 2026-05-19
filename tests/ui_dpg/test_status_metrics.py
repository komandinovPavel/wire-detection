from domain import SourceType
from ui_dpg.adapters.status_metrics import format_frame_badge, source_theme_key


def test_format_frame_badge_shows_placeholder_without_frame_result():
    assert format_frame_badge(SourceType.CAMERA, None) == "Frame: -- ms"


def test_format_frame_badge_shows_live_fps_when_supplied():
    assert format_frame_badge(SourceType.CAMERA, 40.0, fps=25.0) == "Frame: 40.0 ms / 25.0 FPS"
    assert format_frame_badge(SourceType.SCREEN, 50.0, fps=20.0) == "Frame: 50.0 ms / 20.0 FPS"


def test_format_frame_badge_does_not_derive_fps_from_processing_time():
    assert format_frame_badge(SourceType.CAMERA, 0.0, fps=None) == "Frame: 0.0 ms / -- FPS"
    assert format_frame_badge(SourceType.CAMERA, 40.0, fps=None) == "Frame: 40.0 ms / -- FPS"


def test_format_frame_badge_hides_fps_for_still_sources():
    assert format_frame_badge(SourceType.IMAGE, 40.0, fps=25.0) == "Frame: 40.0 ms"
    assert format_frame_badge(SourceType.NONE, 40.0, fps=25.0) == "Frame: 40.0 ms"


def test_format_frame_badge_avoids_invalid_fps_values():
    assert format_frame_badge(SourceType.CAMERA, 0.0) == "Frame: 0.0 ms / -- FPS"
    assert format_frame_badge(SourceType.CAMERA, float("inf")) == "Frame: -- ms"
    assert format_frame_badge(SourceType.CAMERA, float("nan")) == "Frame: -- ms"


def test_source_theme_key_marks_none_as_error_and_active_sources_distinctly():
    assert source_theme_key(SourceType.NONE) == "error"
    assert source_theme_key(SourceType.IMAGE) == "image"
    assert source_theme_key(SourceType.SCREEN) == "screen"
    assert source_theme_key(SourceType.CAMERA) == "camera"
