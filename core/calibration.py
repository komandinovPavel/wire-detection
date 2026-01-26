import cv2
import numpy as np
from typing import Tuple, Optional

class WireCalibrator:
    """Wire diameter calibration and measurement"""
    
    def __init__(self):
        self.pixels_per_mm: Optional[float] = None
        self.calibration_points = []
        self.current_image = None
    
    def set_image(self, image: np.ndarray):
        """Set image for calibration"""
        self.current_image = image.copy()
        self.calibration_points = []
    
    def add_point(self, x: int, y: int):
        """Add calibration point"""
        self.calibration_points.append((x, y))
    
    def calculate_calibration(self, real_distance_mm: float) -> float:
        """Calculate pixels per mm from two points"""
        if len(self.calibration_points) != 2:
            raise ValueError("Need exactly 2 points for calibration")
        
        p1, p2 = self.calibration_points
        pixel_dist = np.hypot(p2[0] - p1[0], p2[1] - p1[1])
        self.pixels_per_mm = pixel_dist / real_distance_mm
        return self.pixels_per_mm
    
    def get_calibration_visual(self, image: np.ndarray) -> np.ndarray:
        """Draw calibration line on image"""
        vis = image.copy()
        
        if len(self.calibration_points) >= 1:
            cv2.circle(vis, self.calibration_points[0], 8, (0, 255, 255), -1)
            cv2.circle(vis, self.calibration_points[0], 12, (0, 255, 255), 2)
        
        if len(self.calibration_points) == 2:
            p1, p2 = self.calibration_points
            cv2.line(vis, p1, p2, (0, 255, 255), 3)
            cv2.circle(vis, p2, 8, (0, 255, 255), -1)
            cv2.circle(vis, p2, 12, (0, 255, 255), 2)
            
            # Show distance in pixels
            mid_x = (p1[0] + p2[0]) // 2
            mid_y = (p1[1] + p2[1]) // 2
            pixel_dist = np.hypot(p2[0] - p1[0], p2[1] - p1[1])
            cv2.putText(vis, f"{pixel_dist:.1f} px", (mid_x + 10, mid_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return vis
    
    def is_calibrated(self) -> bool:
        """Check if calibration is done"""
        return self.pixels_per_mm is not None
    
    def reset_calibration(self):
        """Reset calibration data"""
        self.pixels_per_mm = None
        self.calibration_points = []
    
    def get_calibration_info(self) -> str:
        """Get calibration info string"""
        if not self.is_calibrated():
            return "Not calibrated"
        return f"{self.pixels_per_mm:.3f} px/mm"