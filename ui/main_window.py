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
from core.wire_analyzer import WireAnalyzer

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
        self.wire_analyzer = WireAnalyzer()
        self._calib_clicks = []
        
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
    
    # def on_canvas_click(self, event):
    #     """Handle canvas click during calibration"""
    #     if not self.calibration_mode:
    #         return
        
    #     # Convert display coordinates to original image coordinates
    #     orig_x, orig_y = self.canvas.display_to_original_coords(event.x, event.y)
        
    #     if orig_x is None or orig_y is None:
    #         self.update_status("⚠️ Click inside the image area")
    #         return
        
    #     self.calibrator.add_point(orig_x, orig_y)
        
    #     num_points = len(self.calibrator.calibration_points)
        
    #     # Show point on image
    #     vis = self.calibrator.get_calibration_visual(self.calibration_image)
    #     self.canvas.update_frame(vis)
        
    #     if num_points == 1:
    #         self.update_status(f"📏 Point 1 ({orig_x}, {orig_y}), click second point")
    #     elif num_points == 2:
    #         # Ask for real distance
    #         if self.config.AUTO_CALIBRATION_MODE:
    #             real_dist = self.config.DEFAULT_WIRE_DIAMETER_MM
    #         else:
    #             real_dist = simpledialog.askfloat(
    #                 "Calibration",
    #                 "Enter real distance between the two points (in mm):",
    #                 minvalue=0.1,
    #                 maxvalue=10000.0
    #             )
            
    #         if real_dist:
    #             try:
    #                 px_per_mm = self.calibrator.calculate_calibration(real_dist)
                    
    #                 # Now measure wire diameter automatically
    #                 try:
    #                     diameter_mm, diameter_px = self.measure_wire_width(self.calibration_image, px_per_mm)
                        
    #                     # Add both calibration and wire measurement to image
    #                     vis = self.calibrator.get_calibration_visual(self.calibration_image)
    #                     cv2.putText(vis, f"Calibration: {px_per_mm:.3f} px/mm", 
    #                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    #                     cv2.putText(vis, f"Calibration Distance: {real_dist:.2f} mm", 
    #                                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    #                     cv2.putText(vis, f"Wire Diameter: {diameter_mm:.3f} mm ({diameter_px:.1f} px)", 
    #                                (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                        
    #                     self.canvas.update_frame(vis)
    #                     self.update_status(
    #                         f"✅ Calibrated! Scale: {px_per_mm:.3f} px/mm | Wire: {diameter_mm:.3f}mm"
    #                     )
    #                 except Exception as wire_error:
    #                     # If wire measurement fails, still show calibration
    #                     vis = self.calibrator.get_calibration_visual(self.calibration_image)
    #                     cv2.putText(vis, f"Calibration: {px_per_mm:.3f} px/mm", 
    #                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    #                     cv2.putText(vis, f"Distance: {real_dist:.2f} mm", 
    #                                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    #                     cv2.putText(vis, f"Wire measurement failed: {str(wire_error)[:40]}", 
    #                                (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
    #                     self.canvas.update_frame(vis)
    #                     self.update_status(
    #                         f"✅ Calibrated: {px_per_mm:.3f} px/mm (wire measurement failed)"
    #                     )
                    
    #                 self.calibration_mode = False
                    
    #             except Exception as e:
    #                 self.update_status(f"❌ Calibration error: {e}")
    #                 self.calibrator.reset_calibration()
    #                 self.calibration_mode = False
    #         else:
    #             self.update_status("Calibration cancelled")
    #             self.calibrator.reset_calibration()
    #             self.calibration_mode = False
    
    def on_canvas_click(self, event):
        if not self.calibration_mode:
            return

        orig_x, orig_y = self.canvas.display_to_original_coords(event.x, event.y)
        if orig_x is None:
            self.update_status("⚠️ Click inside the image")
            return

        try:
            diameter_px, top_y, bottom_y = self.wire_analyzer.measure_diameter_at_x(
                self.calibration_image, orig_x
            )

            if diameter_px < 2:
                self.update_status("❌ Could not detect wire edges, try another spot")
                return

            px_per_mm = diameter_px / self.config.NOMINAL_DIAMETER_MM
            self.calibrator.pixels_per_mm = px_per_mm

            mean_diameter_px, _ = self.wire_analyzer.measure(self.calibration_image)
            diameter_mm = mean_diameter_px / px_per_mm

            vis = self._draw_calibration_result(
                self.calibration_image, orig_x, top_y, bottom_y,
                diameter_px, diameter_mm, px_per_mm
            )

            self.canvas.update_frame(vis)

            deviation = diameter_mm - self.config.NOMINAL_DIAMETER_MM
            self.update_status(
                f"✅ Calibrated | Scale: {px_per_mm:.3f} px/mm | "
                f"Measured: {diameter_mm:.3f} mm | "
                f"Deviation: {deviation:+.3f} mm"
            )

        except Exception as e:
            self.update_status(f"❌ Calibration failed: {e}")
        finally:
            self.calibration_mode = False


    def _draw_calibration_result(self, image, orig_x, top_y, bottom_y,
                                diameter_px, diameter_mm, px_per_mm):
        vis = image.copy()
        self._draw_edge_points(vis)
        self._draw_crosshair(vis, orig_x, top_y, bottom_y)
        self._draw_info_panel(vis, orig_x, diameter_px, diameter_mm, px_per_mm)
        return vis


    def _draw_edge_points(self, vis):
        try:
            xs, top_ys, bottom_ys = self.wire_analyzer.get_edge_points(vis)
            for x, ty, by in zip(xs, top_ys, bottom_ys):
                cv2.circle(vis, (int(x), int(ty)), 1, (255, 255, 0), -1)
                cv2.circle(vis, (int(x), int(by)), 1, (0, 165, 255), -1)
        except Exception:
            pass


    def _draw_crosshair(self, vis, orig_x, top_y, bottom_y):
        cross_size = 10

        for y in (top_y, bottom_y):
            cv2.line(vis, (orig_x - cross_size, y), (orig_x + cross_size, y), (0, 0, 255), 2)
            cv2.line(vis, (orig_x, y - cross_size), (orig_x, y + cross_size), (0, 0, 255), 2)

        cv2.line(vis, (orig_x, top_y), (orig_x, bottom_y), (0, 255, 0), 2)

        for label, y in (("TOP", top_y), ("BOT", bottom_y)):
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, th), baseline = cv2.getTextSize(label, font, 0.5, 1)
            tx, ty = orig_x + 12, y + 5

            # Полупрозрачный фон под лейблом
            overlay = vis.copy()
            cv2.rectangle(overlay, (tx - 2, ty - th - 2), (tx + tw + 2, ty + baseline + 2), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, vis, 0.4, 0, vis)

            cv2.putText(vis, label, (tx, ty), font, 0.5, (0, 0, 255), 1)

    def _draw_info_panel(self, vis, orig_x, diameter_px, diameter_mm, px_per_mm):
        deviation = diameter_mm - self.config.NOMINAL_DIAMETER_MM
        indicator_color, indicator_label = self._deviation_indicator(abs(deviation))

        font = cv2.FONT_HERSHEY_SIMPLEX
        lines = [
            ("WIRE CALIBRATION",                                        (200, 200, 200), 0.65, 2),
            ("",                                                        None,            0.4,  1),
            (f"Nominal:    {self.config.NOMINAL_DIAMETER_MM:.3f} mm",   (200, 200, 200), 0.62, 1),
            (f"Measured:   {diameter_mm:.3f} mm",                       (255, 255, 255), 0.62, 1),
            (f"Deviation:  {deviation:+.3f} mm",                        indicator_color, 0.62, 1),
            ("",                                                        None,            0.4,  1),
            (f"Scale:      {px_per_mm:.3f} px/mm",                      (180, 180, 180), 0.58, 1),
            (f"Calib px:   {diameter_px} px  @ x={orig_x}",            (180, 180, 180), 0.58, 1),
        ]

        pad, line_gap = 10, 6
        block_w, block_h = 0, pad

        for text, _, fs, th in lines:
            if not text:
                block_h += 8
                continue
            (tw, lh), baseline = cv2.getTextSize(text, font, fs, th)
            block_w = max(block_w, tw)
            block_h += lh + baseline + line_gap

        block_w += pad * 2

        # Полупрозрачный фон
        overlay = vis.copy()
        cv2.rectangle(overlay, (10, 10), (10 + block_w, 10 + block_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, vis, 0.4, 0, vis)

        # Рамка и цветная полоска
        cv2.rectangle(vis, (10, 10), (10 + block_w, 10 + block_h), (60, 60, 60), 1)
        cv2.rectangle(vis, (10, 10), (14, 10 + block_h), indicator_color, -1)

        # Текст
        y_cursor = 10 + pad
        for text, color, fs, th in lines:
            if not text:
                y_cursor += 8
                continue
            (tw, lh), baseline = cv2.getTextSize(text, font, fs, th)
            cv2.putText(vis, text, (10 + pad + 6, y_cursor + lh), font, fs, color, th)
            y_cursor += lh + baseline + line_gap

        # Плашка индикатора
        (lw, lh), _ = cv2.getTextSize(indicator_label, font, 0.55, 2)
        lx, ly = 10, 10 + block_h + lh + 10   # под блоком, не внутри
        cv2.rectangle(vis, (lx, ly - lh - 4), (lx + lw + 12, ly + 4), indicator_color, -1)
        cv2.putText(vis, indicator_label, (lx + 6, ly), font, 0.55, (0, 0, 0), 2)


    def _deviation_indicator(self, abs_dev: float):
        if abs_dev < self.config.TOLERANCE_OK:
            return (0, 255, 0),   "IN TOLERANCE"
        elif abs_dev < self.config.TOLERANCE_WARN:
            return (0, 200, 255), "WARNING"
        else:
            return (0, 0, 255),   "OUT OF TOLERANCE"    
        
    def measure_wire_width(self, image: np.ndarray, px_per_mm: float):
        diameter_px, _ = self.wire_analyzer.measure(image)
        diameter_mm = diameter_px / px_per_mm
        return diameter_mm, diameter_px
        
    def on_calibrate(self):
        """Start calibration mode"""
        self.stop_capture()
        self._calib_clicks = []
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
            
            self.update_status("📏 Click anywhere on the wire to calibrate")   
                     
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