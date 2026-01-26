from abc import ABC, abstractmethod
import numpy as np

class CaptureSource(ABC):
    """Base interface for capture sources"""
    
    def __init__(self):
        self.running = False
    
    @abstractmethod
    def start(self):
        """Start capture"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop capture"""
        pass
    
    @abstractmethod
    def read_frame(self) -> np.ndarray:
        """Read single frame"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if source is available"""
        pass