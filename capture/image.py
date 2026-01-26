import cv2
import numpy as np
from .base import CaptureSource

class ImageCapture(CaptureSource):
    """Static image loader"""
    
    def __init__(self):
        super().__init__()
        self.image = None
    
    def load(self, filepath: str) -> bool:
        """Load image from file"""
        self.image = cv2.imread(filepath)
        return self.image is not None
    
    def start(self):
        """No-op for static images"""
        self.running = True
        return True
    
    def stop(self):
        """No-op for static images"""
        self.running = False
    
    def read_frame(self) -> np.ndarray:
        """Return loaded image"""
        return self.image
    
    def is_available(self) -> bool:
        """Check if image is loaded"""
        return self.image is not None