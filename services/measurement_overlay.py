from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from domain import CalibrationResult, MeasurementResult


class MeasurementOverlay:
    """Draws calibration and measurement infographics on BGR frames."""

    def render_calibration(self, image: np.ndarray, result: CalibrationResult) -> np.ndarray:
        return self._render(
            image,
            title="WIRE CALIBRATION",
            x=result.x,
            top_y=result.top_y,
            bottom_y=result.bottom_y,
            slope=result.slope,
            diameter_px=result.calibration_diameter_px,
            diameter_mm=result.measured_diameter_mm,
            pixels_per_mm=result.pixels_per_mm,
            nominal_diameter_mm=result.nominal_diameter_mm,
            deviation_mm=result.deviation_mm,
            tolerance_label=result.tolerance_label,
            tolerance_level=result.tolerance_level,
        )

    def render_measurement(self, image: np.ndarray, result: MeasurementResult) -> np.ndarray:
        return self._render(
            image,
            title="WIRE MEASUREMENT",
            x=result.x,
            top_y=result.top_y,
            bottom_y=result.bottom_y,
            slope=result.slope,
            diameter_px=result.diameter_px,
            diameter_mm=result.diameter_mm,
            pixels_per_mm=result.pixels_per_mm,
            nominal_diameter_mm=result.nominal_diameter_mm,
            deviation_mm=result.deviation_mm,
            tolerance_label=result.tolerance_label,
            tolerance_level=result.tolerance_level,
        )

    def _render(
        self,
        image: np.ndarray,
        title: str,
        x: int,
        top_y: int,
        bottom_y: int,
        slope: float,
        diameter_px: float,
        diameter_mm: float,
        pixels_per_mm: float,
        nominal_diameter_mm: float,
        deviation_mm: float,
        tolerance_label: str,
        tolerance_level: str,
    ) -> np.ndarray:
        vis = image.copy()
        color = self._status_color(tolerance_level)
        self._draw_crosshair(vis, x, top_y, bottom_y, slope)
        self._draw_info_panel(
            vis,
            title,
            x,
            diameter_px,
            diameter_mm,
            pixels_per_mm,
            nominal_diameter_mm,
            deviation_mm,
            slope,
            tolerance_label,
            color,
        )
        return vis

    def _draw_crosshair(self, vis: np.ndarray, x: int, top_y: int, bottom_y: int, slope: float) -> None:
        if abs(slope) > 1e-6:
            nx, ny = 1.0, -1.0 / slope
        else:
            nx, ny = 0.0, 1.0

        length = float(np.sqrt(nx**2 + ny**2))
        nx, ny = nx / length, ny / length
        cy = (top_y + bottom_y) // 2
        half_len = max(1.0, (bottom_y - top_y) / 2.0)
        pt1 = (int(x - nx * half_len), int(cy - ny * half_len))
        pt2 = (int(x + nx * half_len), int(cy + ny * half_len))

        cv2.line(vis, pt1, pt2, (0, 255, 0), 2)
        cv2.circle(vis, (int(x), int(cy)), 4, (0, 255, 0), -1)

        font = cv2.FONT_HERSHEY_SIMPLEX
        for label, pt in (("TOP", pt1), ("BOT", pt2)):
            cv2.putText(vis, label, (pt[0] + 8, pt[1] + 4), font, 0.45, (0, 0, 255), 1)

        angle_deg = float(np.degrees(np.arctan(slope)))
        cv2.putText(vis, f"{angle_deg:+.1f} deg", (int(x) + 12, int(cy) - 8), font, 0.45, (220, 220, 220), 1)

    def _draw_info_panel(
        self,
        vis: np.ndarray,
        title: str,
        x: int,
        diameter_px: float,
        diameter_mm: float,
        pixels_per_mm: float,
        nominal_diameter_mm: float,
        deviation_mm: float,
        slope: float,
        tolerance_label: str,
        status_color: tuple[int, int, int],
    ) -> None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        angle_deg = float(np.degrees(np.arctan(slope)))
        lines: list[tuple[str, tuple[int, int, int], float, int]] = [
            (title, (220, 220, 220), 0.62, 2),
            (f"Nominal:   {nominal_diameter_mm:.3f} mm", (210, 210, 210), 0.5, 1),
            (f"Measured:  {diameter_mm:.3f} mm", (255, 255, 255), 0.5, 1),
            (f"Deviation: {deviation_mm:+.3f} mm", status_color, 0.5, 1),
            (f"Scale:     {pixels_per_mm:.2f} px/mm", (180, 180, 180), 0.48, 1),
            (f"Wire px:   {diameter_px:.2f} px @ x={x}", (180, 180, 180), 0.48, 1),
            (f"Slope:     {angle_deg:+.2f} deg", (180, 180, 180), 0.48, 1),
        ]

        pad = 10
        line_gap = 8
        width = 0
        height = pad
        for text, _, scale, thickness in lines:
            (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
            width = max(width, text_w)
            height += text_h + baseline + line_gap
        width += pad * 2

        overlay = vis.copy()
        cv2.rectangle(overlay, (10, 10), (10 + width, 10 + height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.62, vis, 0.38, 0, vis)
        cv2.rectangle(vis, (10, 10), (10 + width, 10 + height), (70, 70, 70), 1)
        cv2.rectangle(vis, (10, 10), (14, 10 + height), status_color, -1)

        y = 10 + pad
        for text, color, scale, thickness in lines:
            (_, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
            cv2.putText(vis, text, (10 + pad + 6, y + text_h), font, scale, color, thickness)
            y += text_h + baseline + line_gap

        (label_w, label_h), _ = cv2.getTextSize(tolerance_label, font, 0.5, 2)
        label_y = 10 + height + label_h + 8
        cv2.rectangle(vis, (10, label_y - label_h - 4), (10 + label_w + 12, label_y + 4), status_color, -1)
        cv2.putText(vis, tolerance_label, (16, label_y), font, 0.5, (0, 0, 0), 2)

    def _status_color(self, tolerance_level: str) -> tuple[int, int, int]:
        colors: dict[str, tuple[int, int, int]] = {
            "ok": (0, 210, 0),
            "warn": (0, 200, 255),
            "error": (0, 0, 255),
        }
        return colors.get(tolerance_level, (220, 220, 220))
