from pathlib import Path

class Config:
    """Application configuration"""
    
    # Model settings
    MODEL_PATH = "runs/segment/wire_defects/v1/weights/best.pt"
    DEFAULT_IMGSZ = 640
    DEFAULT_CONFIDENCE = 0.3
    
    # UI settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    CANVAS_BG = "black"
    
    # Colors
    COLOR_BG = "#2b2b2b"
    COLOR_STATUS_BG = "#1e1e1e"
    COLOR_STATUS_FG = "#00ff00"
    COLOR_BTN_IMAGE = "#4CAF50"
    COLOR_BTN_SCREEN = "#2196F3"
    COLOR_BTN_CAMERA = "#FF9800"
    COLOR_BTN_STOP = "#f44336"
    
    # Camera detection
    MAX_CAMERA_INDEX = 10