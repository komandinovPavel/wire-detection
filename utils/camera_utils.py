import cv2
from typing import List

def detect_available_cameras(max_index: int = 10) -> List[str]:
    """Detect all available cameras"""
    available = []
    print("🔍 Detecting cameras...")
    
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                backend = cap.getBackendName()
                available.append(f"Camera {i} ({backend})")
                print(f"  ✅ Found: Camera {i}")
            cap.release()
    
    if not available:
        print("  ⚠️ No cameras found, adding default")
        available.append("Camera 0 (default)")
    
    return available

def parse_camera_index(camera_str: str) -> int:
    """Extract camera index from string like 'Camera 0 (backend)'"""
    try:
        return int(camera_str.split()[1])
    except (IndexError, ValueError):
        return 0