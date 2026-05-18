import numpy as np

from services.calibration_service import CalibrationService


class StubWireAnalyzer:
    def __init__(self):
        self.measure_at_calls = []
        self.measure_calls = []

    def measure_diameter_at_x(self, image, x_coord):
        self.measure_at_calls.append((image, x_coord))
        return 188.0, 20, 208, 0.1

    def measure(self, image):
        self.measure_calls.append(image)
        return 190.0, np.array([189.0, 190.0, 191.0])


def test_calibrate_at_sets_pixels_per_mm_from_nominal_diameter():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    analyzer = StubWireAnalyzer()
    service = CalibrationService(
        analyzer=analyzer,
        nominal_diameter_mm=1.88,
        tolerance_ok=0.03,
        tolerance_warn=0.07,
    )

    result = service.calibrate_at(image, x=100)

    assert result.pixels_per_mm == 100.0
    assert result.calibration_diameter_px == 188.0
    assert result.measured_diameter_mm == 1.9
    assert service.is_calibrated() is True
    assert service.pixels_per_mm == 100.0
    assert analyzer.measure_at_calls == [(image, 100)]
    assert analyzer.measure_calls == [image]


def test_measure_at_requires_calibration():
    service = CalibrationService(analyzer=StubWireAnalyzer())

    try:
        service.measure_at(np.zeros((5, 5, 3), dtype=np.uint8), x=10)
    except RuntimeError as exc:
        assert "Not calibrated" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_measure_at_uses_existing_scale():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    service = CalibrationService(
        analyzer=StubWireAnalyzer(),
        nominal_diameter_mm=1.88,
    )
    service.calibrate_at(image, x=100)

    result = service.measure_at(image, x=120)

    assert result.x == 120
    assert result.diameter_px == 188.0
    assert result.diameter_mm == 1.88
    assert result.pixels_per_mm == 100.0


def test_reset_clears_calibration_scale():
    service = CalibrationService(analyzer=StubWireAnalyzer(), nominal_diameter_mm=1.88)
    service.calibrate_at(np.zeros((10, 10, 3), dtype=np.uint8), x=100)

    service.reset()

    assert service.is_calibrated() is False
    assert service.pixels_per_mm is None
