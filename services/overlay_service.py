from __future__ import annotations

from typing import Any


class OverlayService:
    """Owns visual overlay operations as the project grows."""

    def passthrough(self, frame: Any) -> Any:
        return frame
