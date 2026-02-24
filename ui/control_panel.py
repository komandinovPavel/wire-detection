import tkinter as tk
from tkinter import ttk
from typing import Callable, List

class ControlPanel:
    """Control panel with buttons and settings"""
    
    def __init__(self, parent, config):
        self.config = config
        self.frame = tk.Frame(parent, bg=config.COLOR_BG, height=80)
        self.frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.camera_combo = None
        self.conf_scale = None
        
        self._setup_controls()
    
    def _setup_controls(self):
        """Setup control buttons and widgets"""
        btn_style = {"font": ("Arial", 10), "width": 13, "height": 2}
        
        # Row 0: Main controls
        self.btn_load = tk.Button(self.frame, text="📁 Load Image", 
                                   bg=self.config.COLOR_BTN_IMAGE, fg="white", **btn_style)
        self.btn_load.grid(row=0, column=0, padx=5, pady=5)
        
        self.btn_screen = tk.Button(self.frame, text="🖥️ Screen", 
                                     bg=self.config.COLOR_BTN_SCREEN, fg="white", **btn_style)
        self.btn_screen.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_camera = tk.Button(self.frame, text="📷 Camera", 
                                     bg=self.config.COLOR_BTN_CAMERA, fg="white", **btn_style)
        self.btn_camera.grid(row=0, column=2, padx=5, pady=5)
        
        self.btn_stop = tk.Button(self.frame, text="⏹️ Stop", 
                                   bg=self.config.COLOR_BTN_STOP, fg="white", **btn_style)
        self.btn_stop.grid(row=0, column=3, padx=5, pady=5)
        
        # Calibration button
        self.btn_calibrate = tk.Button(self.frame, text="📏 Calibrate",
                                        bg="#9C27B0", fg="white", **btn_style)
        self.btn_calibrate.grid(row=0, column=4, padx=5, pady=5)

        self.btn_measure = tk.Button(self.frame, text="📐 Measure",
                                    bg="#1565C0", fg="white", **btn_style,
                                    state=tk.DISABLED)  # недоступна пока нет калибровки
        self.btn_measure.grid(row=0, column=5, padx=5, pady=5)
        
        # Camera selector
        tk.Label(self.frame, text="Camera:", bg=self.config.COLOR_BG, 
                fg="white", font=("Arial", 10)).grid(row=0, column=6, padx=5)
        self.camera_combo = ttk.Combobox(self.frame, width=18, state="readonly")
        self.camera_combo.grid(row=0, column=6, padx=5)
        
        # Confidence slider
        tk.Label(self.frame, text="Confidence:", bg=self.config.COLOR_BG, 
                fg="white", font=("Arial", 10)).grid(row=0, column=8, padx=5)
        self.conf_scale = tk.Scale(self.frame, from_=0.1, to=0.9, resolution=0.05,
                                    orient=tk.HORIZONTAL, bg=self.config.COLOR_BG, 
                                    fg="white", length=120)
        self.conf_scale.set(self.config.DEFAULT_CONFIDENCE)
        self.conf_scale.grid(row=0, column=8, padx=5)
    
    def set_camera_list(self, cameras: List[str]):
        """Set available cameras"""
        self.camera_combo['values'] = cameras
        if cameras:
            self.camera_combo.set(cameras[0])
    
    def get_selected_camera(self) -> str:
        """Get selected camera string"""
        return self.camera_combo.get()
    
    def get_confidence(self) -> float:
        """Get confidence threshold"""
        return self.conf_scale.get()
    
    def set_calibration_state(self, state: str):
        """
        state: 'idle' | 'calibrating' | 'measuring'
        """
        styles = {
            "idle":        ("📏 Calibrate", "#9C27B0"),
            "calibrating": ("📏 Calibrating...", "#E65100"),
            "measuring":   ("📐 Measuring",  "#1565C0"),
        }
        text, color = styles.get(state, styles["idle"])
        self.btn_calibrate.config(text=text, bg=color)
    
    def enable_measure(self):
        self.btn_measure.config(state=tk.NORMAL)
    
    def disable_measure(self):
        self.btn_measure.config(state=tk.DISABLED)


    def set_active_mode(self, mode: str):
        """mode: 'calibrate' | 'measure' | None"""
        self.btn_calibrate.config(relief=tk.SUNKEN if mode == "calibrate" else tk.RAISED)
        self.btn_measure.config(relief=tk.SUNKEN if mode == "measure" else tk.RAISED)