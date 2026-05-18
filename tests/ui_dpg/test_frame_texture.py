import numpy as np

from ui_dpg.adapters.frame_texture import bgr_frame_to_rgba_float, fit_size


def test_bgr_frame_to_rgba_float_converts_channels_and_range():
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    frame[0, 0] = [255, 128, 0]

    data = bgr_frame_to_rgba_float(frame)

    assert data == [0.0, 128 / 255.0, 1.0, 1.0]


def test_fit_size_preserves_aspect_ratio():
    assert fit_size(1920, 1080, 960, 540) == (960, 540)
    assert fit_size(1920, 1080, 500, 500) == (500, 281)
