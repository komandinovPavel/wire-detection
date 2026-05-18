from __future__ import annotations

from typing import Any

from core.config import Config
from core.wire_analyzer import WireAnalyzer
from domain import CalibrationResult, MeasurementResult


class CalibrationService:
    """Calibrates pixel scale and measures wire diameter on still frames."""

    def __init__(
        self,
        analyzer: Any | None = None,
        nominal_diameter_mm: float = Config.NOMINAL_DIAMETER_MM,
        tolerance_ok: float = Config.TOLERANCE_OK,
        tolerance_warn: float = Config.TOLERANCE_WARN,
    ):
        self._analyzer = analyzer or WireAnalyzer()
        self._nominal_diameter_mm = float(nominal_diameter_mm)
        self._tolerance_ok = float(tolerance_ok)
        self._tolerance_warn = float(tolerance_warn)
        self.pixels_per_mm: float | None = None

    def is_calibrated(self) -> bool:
        return self.pixels_per_mm is not None

    def calibrate_at(self, image: Any, x: int) -> CalibrationResult:
        diameter_px, top_y, bottom_y, slope = self._analyzer.measure_diameter_at_x(image, x)
        if diameter_px <= 0:
            raise RuntimeError("Calibration diameter must be positive")

        pixels_per_mm = float(diameter_px) / self._nominal_diameter_mm
        self.pixels_per_mm = pixels_per_mm
        measured_diameter_px, _ = self._analyzer.measure(image)
        measured_diameter_mm = float(measured_diameter_px) / pixels_per_mm

        return CalibrationResult(
            x=int(x),
            calibration_diameter_px=float(diameter_px),
            measured_diameter_px=float(measured_diameter_px),
            measured_diameter_mm=measured_diameter_mm,
            pixels_per_mm=pixels_per_mm,
            top_y=int(top_y),
            bottom_y=int(bottom_y),
            slope=float(slope),
            nominal_diameter_mm=self._nominal_diameter_mm,
            tolerance_ok=self._tolerance_ok,
            tolerance_warn=self._tolerance_warn,
        )

    def measure_at(self, image: Any, x: int) -> MeasurementResult:
        if self.pixels_per_mm is None:
            raise RuntimeError("Not calibrated")

        diameter_px, top_y, bottom_y, slope = self._analyzer.measure_diameter_at_x(image, x)
        diameter_mm = float(diameter_px) / self.pixels_per_mm
        return MeasurementResult(
            x=int(x),
            diameter_px=float(diameter_px),
            diameter_mm=diameter_mm,
            pixels_per_mm=self.pixels_per_mm,
            top_y=int(top_y),
            bottom_y=int(bottom_y),
            slope=float(slope),
            nominal_diameter_mm=self._nominal_diameter_mm,
            tolerance_ok=self._tolerance_ok,
            tolerance_warn=self._tolerance_warn,
        )

    def reset(self) -> None:
        self.pixels_per_mm = None
