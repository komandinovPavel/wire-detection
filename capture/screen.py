import numpy as np
import mss
from .base import CaptureSource
import cv2

class ScreenCapture(CaptureSource):
    """Screen capture implementation"""
    
    def __init__(self):
        super().__init__()
        self.monitor_index = 1  # Primary monitor
    
    def start(self):
        """Start screen capture"""
        self.running = True
        return True
    
    def stop(self):
        """Stop screen capture"""
        self.running = False
    
    def read_frame(self) -> np.ndarray:
        """Capture screen frame - creates mss instance per thread"""
        if not self.running:
            return None
        
        try:
            # IMPORTANT: Create mss instance inside the thread to avoid _thread._local error
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_index]
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)[:, :, :3]
                return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if screen capture is running"""
        return self.running