from ultralytics import YOLO
from pathlib import Path
import numpy as np
from typing import List, Dict

class DefectDetector:
    """YOLO model wrapper for defect detection"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load YOLO model"""
        try:
            if Path(self.model_path).exists():
                self.model = YOLO(self.model_path)
                print(f"✅ Model loaded: {self.model_path}")
            else:
                print(f"⚠️ Model not found: {self.model_path}")
        except Exception as e:
            print(f"❌ Model loading error: {e}")
    
    def predict(self, frame: np.ndarray, conf: float = 0.3, imgsz: int = 640):
        """Run inference on frame
        
        Returns:
            tuple: (annotated_frame, detections_list)
        """
        if self.model is None:
            return frame, []
        
        try:
            results = self.model(frame, imgsz=imgsz, conf=conf, verbose=False)
            result = results[0]
            
            # Parse detections
            detections = []
            if result.boxes is not None:
                for box in result.boxes:
                    detection = {
                        'class': result.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist()
                    }
                    detections.append(detection)
            
            annotated = result.plot()
            return annotated, detections
            
        except Exception as e:
            print(f"Inference error: {e}")
            return frame, []
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None