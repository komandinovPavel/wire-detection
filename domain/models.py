from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Mapping, Sequence

from .enums import AppMode, RuntimeStatus, SourceType


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox: Sequence[float]
    timestamp: float = field(default_factory=perf_counter)

    def __post_init__(self) -> None:
        if len(self.bbox) != 4:
            raise ValueError("Detection bbox must contain exactly 4 values")
        normalized = tuple(float(value) for value in self.bbox)
        object.__setattr__(self, "bbox", normalized)


@dataclass(frozen=True)
class DetectionResult:
    annotated_frame: Any
    detections: list[Detection]
    error: str | None = None


@dataclass(frozen=True)
class ProcessingSettings:
    confidence: float = 0.3
    imgsz: int = 640
    deduplicate_defects: bool = True


@dataclass(frozen=True)
class DefectStats:
    total: int = 0
    by_class: Mapping[str, int] = field(default_factory=dict)


def _tolerance_level(abs_deviation: float, tolerance_ok: float, tolerance_warn: float) -> tuple[str, str]:
    if abs_deviation < tolerance_ok:
        return "ok", "IN TOLERANCE"
    if abs_deviation < tolerance_warn:
        return "warn", "WARNING"
    return "error", "OUT OF TOLERANCE"


@dataclass(frozen=True)
class MeasurementResult:
    x: int
    diameter_px: float
    diameter_mm: float
    pixels_per_mm: float
    top_y: int
    bottom_y: int
    slope: float
    nominal_diameter_mm: float
    tolerance_ok: float
    tolerance_warn: float
    deviation_mm: float = field(init=False)
    tolerance_level: str = field(init=False)
    tolerance_label: str = field(init=False)

    def __post_init__(self) -> None:
        deviation = round(float(self.diameter_mm - self.nominal_diameter_mm), 6)
        level, label = _tolerance_level(abs(deviation), self.tolerance_ok, self.tolerance_warn)
        object.__setattr__(self, "deviation_mm", deviation)
        object.__setattr__(self, "tolerance_level", level)
        object.__setattr__(self, "tolerance_label", label)


@dataclass(frozen=True)
class CalibrationResult:
    x: int
    calibration_diameter_px: float
    measured_diameter_px: float
    measured_diameter_mm: float
    pixels_per_mm: float
    top_y: int
    bottom_y: int
    slope: float
    nominal_diameter_mm: float
    tolerance_ok: float
    tolerance_warn: float
    deviation_mm: float = field(init=False)
    tolerance_level: str = field(init=False)
    tolerance_label: str = field(init=False)

    def __post_init__(self) -> None:
        deviation = round(float(self.measured_diameter_mm - self.nominal_diameter_mm), 6)
        level, label = _tolerance_level(abs(deviation), self.tolerance_ok, self.tolerance_warn)
        object.__setattr__(self, "deviation_mm", deviation)
        object.__setattr__(self, "tolerance_level", level)
        object.__setattr__(self, "tolerance_label", label)


@dataclass(frozen=True)
class FrameResult:
    source_frame: Any = None
    display_frame: Any = None
    detections: list[Detection] = field(default_factory=list)
    new_detections: list[Detection] = field(default_factory=list)
    stats: DefectStats = field(default_factory=DefectStats)
    status: RuntimeStatus = RuntimeStatus.READY
    message: str = ""
    error: str | None = None
    processing_ms: float = 0.0

    @classmethod
    def error(cls, message: str, source_frame: Any = None) -> "FrameResult":
        return cls(
            source_frame=source_frame,
            display_frame=source_frame,
            status=RuntimeStatus.ERROR,
            message=message,
            error=message,
        )


@dataclass(frozen=True)
class RuntimeSnapshot:
    status: RuntimeStatus
    source_type: SourceType
    mode: AppMode
    message: str
    settings: ProcessingSettings
    stats: DefectStats
    last_error: str | None = None
