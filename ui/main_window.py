import tkinter as tk
from tkinter import filedialog, simpledialog
import threading
from typing import Optional

import cv2
import numpy as np
from core.calibration import WireCalibrator
from ui.control_panel import ControlPanel
from ui.display_canvas import DisplayCanvas
from ui.defect_panel import DefectPanel
from core.config import Config
from core.model import DefectDetector
from capture.camera import CameraCapture
from capture.screen import ScreenCapture
from capture.image import ImageCapture
from utils.camera_utils import detect_available_cameras, parse_camera_index

class MainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.config = Config()
        
        # Setup window
        self.root.title("Wire Defect Detector - MVP")
        self.root.geometry(f"{self.config.WINDOW_WIDTH}x{self.config.WINDOW_HEIGHT}")
        
        # Model & Calibration
        self.detector = DefectDetector(self.config.MODEL_PATH)
        self.calibrator = WireCalibrator()
        
        # Capture sources
        self.current_capture: Optional[object] = None
        self.capture_thread: Optional[threading.Thread] = None
        
        # Calibration state
        self.calibration_mode = False
        self.calibration_image = None
        
        # Thread-safe cache for confidence value
        self._confidence_cache = self.config.DEFAULT_CONFIDENCE
        self._confidence_lock = threading.Lock()
        
        # UI Components
        self.control_panel = ControlPanel(self.root, self.config)
        
        # Container for canvas and defect panel
        self.main_container = tk.Frame(self.root, bg="#1e1e1e")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # IMPORTANT: Pack defect panel FIRST (right side), then canvas (fills rest)
        self.defect_panel = DefectPanel(self.main_container, self.config)
        self.canvas = DisplayCanvas(self.main_container)
        
        self.status_label = self._create_status_bar()
        
        # Setup
        self._setup_cameras()
        self._bind_controls()
        
        # Bind canvas clicks for calibration
        self.canvas.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Start confidence updater
        self._update_confidence_cache()
        
        self.update_status("Ready")
    
    def on_canvas_click(self, event):
        """Handle canvas click during calibration"""
        if not self.calibration_mode:
            return
        
        # Convert display coordinates to original image coordinates
        orig_x, orig_y = self.canvas.display_to_original_coords(event.x, event.y)
        
        if orig_x is None or orig_y is None:
            self.update_status("⚠️ Click inside the image area")
            return
        
        self.calibrator.add_point(orig_x, orig_y)
        
        num_points = len(self.calibrator.calibration_points)
        
        # Show point on image
        vis = self.calibrator.get_calibration_visual(self.calibration_image)
        self.canvas.update_frame(vis)
        
        if num_points == 1:
            self.update_status(f"📏 Point 1 ({orig_x}, {orig_y}), click second point")
        elif num_points == 2:
            # Ask for real distance
            real_dist = simpledialog.askfloat(
                "Calibration",
                "Enter real distance between the two points (in mm):",
                minvalue=0.1,
                maxvalue=10000.0
            )
            
            if real_dist:
                try:
                    px_per_mm = self.calibrator.calculate_calibration(real_dist)
                    
                    # Now measure wire diameter automatically
                    try:
                        diameter_mm, diameter_px = self.measure_wire_width(self.calibration_image, px_per_mm)
                        
                        # Add both calibration and wire measurement to image
                        vis = self.calibrator.get_calibration_visual(self.calibration_image)
                        cv2.putText(vis, f"Calibration: {px_per_mm:.3f} px/mm", 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(vis, f"Calibration Distance: {real_dist:.2f} mm", 
                                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(vis, f"Wire Diameter: {diameter_mm:.3f} mm ({diameter_px:.1f} px)", 
                                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                        
                        self.canvas.update_frame(vis)
                        self.update_status(
                            f"✅ Calibrated! Scale: {px_per_mm:.3f} px/mm | Wire: {diameter_mm:.3f}mm"
                        )
                    except Exception as wire_error:
                        # If wire measurement fails, still show calibration
                        vis = self.calibrator.get_calibration_visual(self.calibration_image)
                        cv2.putText(vis, f"Calibration: {px_per_mm:.3f} px/mm", 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(vis, f"Distance: {real_dist:.2f} mm", 
                                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(vis, f"Wire measurement failed: {str(wire_error)[:40]}", 
                                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        self.canvas.update_frame(vis)
                        self.update_status(
                            f"✅ Calibrated: {px_per_mm:.3f} px/mm (wire measurement failed)"
                        )
                    
                    self.calibration_mode = False
                    
                except Exception as e:
                    self.update_status(f"❌ Calibration error: {e}")
                    self.calibrator.reset_calibration()
                    self.calibration_mode = False
            else:
                self.update_status("Calibration cancelled")
                self.calibrator.reset_calibration()
                self.calibration_mode = False
    
    def measure_wire_width(self, image: np.ndarray, px_per_mm: float):
        """Measure wire diameter using edge detection
        
        Args:
            image: Color image
            px_per_mm: Calibration factor
            
        Returns:
            tuple: (diameter_mm, diameter_px)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            raise RuntimeError("No wire contour found")
        
        # Get largest contour (should be the wire)
        wire_contour = max(contours, key=cv2.contourArea)
        
        # Create mask from contour
        mask = np.zeros_like(binary)
        cv2.drawContours(mask, [wire_contour], -1, 255, -1)
        
        # Use distance transform to find the thickest part
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        _, max_radius_px, _, center = cv2.minMaxLoc(dist_transform)
        
        # Diameter in pixels (radius * 2)
        diameter_px = max_radius_px * 2
        
        # Convert to mm
        diameter_mm = diameter_px / px_per_mm
        
        return diameter_mm, diameter_px
    
    def on_calibrate(self):
        """Start calibration mode"""
        self.stop_capture()
        
        # Load image for calibration
        filepath = filedialog.askopenfilename(
            title="Select Image for Calibration",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Load image (color)
            img_array = np.fromfile(filepath, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                self.update_status("Error loading image")
                return
            
            # Store original image
            self.calibration_image = img
            
            # Show image
            self.canvas.update_frame(img)
            
            # Enter calibration mode
            self.calibration_mode = True
            self.calibrator.set_image(img)
            
            self.update_status("📏 Calibration Mode: Click two points of known distance")
            
        except Exception as e:
            self.update_status(f"Calibration error: {e}")
            self.calibration_mode = False
    
    def _update_confidence_cache(self):
        """Periodically cache confidence value in thread-safe way"""
        try:
            conf = self.control_panel.conf_scale.get()
            with self._confidence_lock:
                self._confidence_cache = conf
        except:
            pass  # Ignore Tkinter errors during updates
        
        # Schedule next update
        self.root.after(100, self._update_confidence_cache)
    
    def _get_confidence(self) -> float:
        """Thread-safe get confidence value"""
        with self._confidence_lock:
            return self._confidence_cache
    
    def _create_status_bar(self):
        """Create status bar"""
        label = tk.Label(self.root, text="Status: Ready", 
                        bg=self.config.COLOR_STATUS_BG, 
                        fg=self.config.COLOR_STATUS_FG,
                        font=("Consolas", 10), anchor="w")
        label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        return label
    
    def _setup_cameras(self):
        """Detect and setup available cameras"""
        cameras = detect_available_cameras(self.config.MAX_CAMERA_INDEX)
        self.control_panel.set_camera_list(cameras)
    
    def _bind_controls(self):
        """Bind button callbacks"""
        self.control_panel.btn_load.config(command=self.on_load_image)
        self.control_panel.btn_screen.config(command=self.on_screen_capture)
        self.control_panel.btn_camera.config(command=self.on_camera_capture)
        self.control_panel.btn_stop.config(command=self.on_stop)
        self.control_panel.btn_calibrate.config(command=self.on_calibrate)
        self.control_panel.camera_combo.bind("<<ComboboxSelected>>", self.on_camera_change)
    
    def update_status(self, message: str):
        """Update status bar"""
        self.status_label.config(text=f"Status: {message}")
    
    def on_load_image(self):
        """Load static image"""
        self.stop_capture()
        
        filepath = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")]
        )
        
        if filepath:
            capture = ImageCapture()
            if capture.load(filepath):
                frame = capture.read_frame()
                processed, detections = self.detector.predict(
                    frame, 
                    self._get_confidence(),
                    self.config.DEFAULT_IMGSZ
                )
                self.canvas.update_frame(processed)
                self.defect_panel.update_defects(detections)
                self.update_status(f"Image loaded: {filepath} | Defects: {len(detections)}")
            else:
                self.update_status("Error loading image")
    
    def on_screen_capture(self):
        """Start screen capture"""
        self.stop_capture()
        self.current_capture = ScreenCapture()
        if self.current_capture.start():
            self.update_status("Screen capture active")
            self._start_capture_loop()
    
    def on_camera_capture(self):
        """Start camera capture"""
        self.stop_capture()
        
        camera_str = self.control_panel.get_selected_camera()
        camera_idx = parse_camera_index(camera_str)
        
        self.current_capture = CameraCapture(camera_idx)
        if self.current_capture.start():
            self.update_status(f"{camera_str} active")
            self._start_capture_loop()
        else:
            self.update_status(f"Error opening {camera_str}")
    
    def on_camera_change(self, event):
        """Handle camera change"""
        if isinstance(self.current_capture, CameraCapture) and self.current_capture.running:
            self.update_status("Switching camera...")
            self.on_camera_capture()
    
    def on_stop(self):
        """Stop capture"""
        self.stop_capture()
        self.update_status("Capture stopped")
    
    def stop_capture(self):
        """Stop current capture"""
        if self.current_capture:
            self.current_capture.stop()
            self.current_capture = None
    
    def _start_capture_loop(self):
        """Start capture thread"""
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
    
    def _capture_loop(self):
        """Main capture loop"""
        while self.current_capture and self.current_capture.running:
            frame = self.current_capture.read_frame()
            if frame is not None:
                processed, detections = self.detector.predict(
                    frame,
                    self._get_confidence(),
                    self.config.DEFAULT_IMGSZ
                )
                self.canvas.update_frame(processed)
                
                # Update defect panel only if new defects found
                if detections:
                    self.defect_panel.update_defects(detections)
    
    def on_closing(self):
        """Handle window close"""
        self.stop_capture()
        self.root.destroy()