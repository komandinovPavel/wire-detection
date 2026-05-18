from __future__ import annotations

from dataclasses import dataclass, field

from domain import AppMode, DefectStats, ProcessingSettings, RuntimeSnapshot, RuntimeStatus, SourceType


@dataclass
class AppState:
    settings: ProcessingSettings = field(default_factory=ProcessingSettings)
    status: RuntimeStatus = RuntimeStatus.IDLE
    source_type: SourceType = SourceType.NONE
    mode: AppMode = AppMode.DETECT
    message: str = "Ready"
    last_error: str | None = None
    stats: DefectStats = field(default_factory=DefectStats)

    def snapshot(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            status=self.status,
            source_type=self.source_type,
            mode=self.mode,
            message=self.message,
            settings=self.settings,
            stats=self.stats,
            last_error=self.last_error,
        )
