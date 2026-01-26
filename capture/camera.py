import cv2
import numpy as np
from .base import CaptureSource

class CameraCapture(CaptureSource):
    """Camera capture implementation"""
    
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
    
    def start(self):
        """Start camera capture"""
        self.stop()  # Ensure previous is closed
        self.cap = cv2.VideoCapture(self.camera_index)
        self.running = self.cap.isOpened()
        return self.running
    
    def stop(self):
        """Stop camera capture"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def read_frame(self) -> np.ndarray:
        """Read frame from camera"""
        if not self.running or not self.cap:
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def is_available(self) -> bool:
        """Check if camera is available"""
        return self.running and self.cap is not None