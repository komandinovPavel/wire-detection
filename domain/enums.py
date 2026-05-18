from enum import Enum


class SourceType(str, Enum):
    NONE = "none"
    IMAGE = "image"
    SCREEN = "screen"
    CAMERA = "camera"


class AppMode(str, Enum):
    DETECT = "detect"
    CALIBRATE = "calibrate"
    MEASURE = "measure"


class RuntimeStatus(str, Enum):
    IDLE = "idle"
    LOADING_MODEL = "loading_model"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
