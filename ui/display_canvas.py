import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import cv2

class DisplayCanvas:
    """Canvas for displaying processed frames"""
    
    def __init__(self, parent):
        self.canvas = tk.Canvas(parent, bg="black")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        self.current_image = None
        
        # Store scaling info for coordinate conversion
        self.display_width = 0
        self.display_height = 0
        self.original_width = 0
        self.original_height = 0
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
    
    def update_frame(self, frame: np.ndarray):
        """Update canvas with new frame"""
        if frame is None:
            return
        
        # Store original dimensions
        self.original_height, self.original_width = frame.shape[:2]
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Calculate scaling to fit canvas while maintaining aspect ratio
            scale_w = canvas_width / self.original_width
            scale_h = canvas_height / self.original_height
            self.scale = min(scale_w, scale_h)
            
            # Calculate display dimensions
            self.display_width = int(self.original_width * self.scale)
            self.display_height = int(self.original_height * self.scale)
            
            # Calculate offset to center image
            self.offset_x = (canvas_width - self.display_width) // 2
            self.offset_y = (canvas_height - self.display_height) // 2
            
            # Resize image
            img = img.resize((self.display_width, self.display_height), Image.Resampling.LANCZOS)
        
        # Update canvas
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width//2, canvas_height//2, image=imgtk)
        self.canvas.image = imgtk  # Keep reference
    
    def display_to_original_coords(self, display_x: int, display_y: int) -> tuple:
        """Convert display coordinates to original image coordinates"""
        # Remove offset
        rel_x = display_x - self.offset_x
        rel_y = display_y - self.offset_y
        
        # Check if click is within image bounds
        if rel_x < 0 or rel_y < 0 or rel_x > self.display_width or rel_y > self.display_height:
            return None, None
        
        # Scale to original coordinates
        orig_x = int(rel_x / self.scale)
        orig_y = int(rel_y / self.scale)
        
        # Clamp to image bounds
        orig_x = max(0, min(orig_x, self.original_width - 1))
        orig_y = max(0, min(orig_y, self.original_height - 1))
        
        return orig_x, orig_y
    
    def clear(self):
        """Clear canvas"""
        self.canvas.delete("all")