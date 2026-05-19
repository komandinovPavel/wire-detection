from __future__ import annotations

import cv2


def is_camera_available(index: int) -> bool:
    """Return True when OpenCV can open a camera index."""
    capture = cv2.VideoCapture(index)
    try:
        return bool(capture.isOpened())
    finally:
        capture.release()


def detect_available_camera_indices(max_index: int = 10) -> list[int]:
    """Detect available OpenCV camera indices."""
    return [index for index in range(max_index) if is_camera_available(index)]


def detect_available_cameras(max_index: int = 10) -> list[str]:
    """Return display labels for available cameras."""
    cameras = []
    for index in detect_available_camera_indices(max_index):
        cameras.append(f"Camera {index}")
    return cameras or ["Camera 0"]


def parse_camera_index(camera_str: str) -> int:
    """Extract camera index from string like 'Camera 0 (backend)'"""
    try:
        return int(camera_str.split()[1])
    except (IndexError, ValueError):
        return 0
