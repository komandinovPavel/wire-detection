import numpy as np

from domain import CalibrationResult, MeasurementResult
from services.measurement_overlay import MeasurementOverlay


def test_render_calibration_returns_overlay_with_same_shape():
    image = np.zeros((120, 240, 3), dtype=np.uint8)
    result = CalibrationResult(
        x=80,
        calibration_diameter_px=60.0,
        measured_diameter_px=61.0,
        measured_diameter_mm=1.9,
        pixels_per_mm=32.0,
        top_y=40,
        bottom_y=100,
        slope=0.0,
        nominal_diameter_mm=1.88,
        tolerance_ok=0.03,
        tolerance_warn=0.07,
    )

    overlay = MeasurementOverlay().render_calibration(image, result)

    assert overlay.shape == image.shape
    assert overlay.dtype == image.dtype
    assert np.any(overlay != image)


def test_render_measurement_returns_overlay_with_same_shape():
    image = np.zeros((120, 240, 3), dtype=np.uint8)
    result = MeasurementResult(
        x=80,
        diameter_px=60.0,
        diameter_mm=1.9,
        pixels_per_mm=32.0,
        top_y=40,
        bottom_y=100,
        slope=0.0,
        nominal_diameter_mm=1.88,
        tolerance_ok=0.03,
        tolerance_warn=0.07,
    )

    overlay = MeasurementOverlay().render_measurement(image, result)

    assert overlay.shape == image.shape
    assert overlay.dtype == image.dtype
    assert np.any(overlay != image)
