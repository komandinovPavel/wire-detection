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
