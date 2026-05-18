import numpy as np

from ui_dpg.adapters.frame_texture import bgr_frame_to_rgba_float, fit_size, map_display_to_source


def test_bgr_frame_to_rgba_float_converts_channels_and_range():
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    frame[0, 0] = [255, 128, 0]

    data = bgr_frame_to_rgba_float(frame)

    assert data == [0.0, 128 / 255.0, 1.0, 1.0]


def test_fit_size_preserves_aspect_ratio():
    assert fit_size(1920, 1080, 960, 540) == (960, 540)
    assert fit_size(1920, 1080, 500, 500) == (500, 281)


def test_map_display_to_source_scales_and_clamps_coordinates():
    assert map_display_to_source(50, 25, 200, 100, 100, 50) == (100, 50)
    assert map_display_to_source(-5, 80, 200, 100, 100, 50) == (0, 99)
