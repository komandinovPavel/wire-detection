import tkinter as tk
from tkinter import ttk
from typing import Dict, List
from datetime import datetime

class DefectPanel:
    """Side panel for displaying detected defects"""
    
    def __init__(self, parent, config):
        self.config = config
        
        # Main frame
        self.frame = tk.Frame(parent, bg=config.COLOR_BG, width=320)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 10), pady=10)
        self.frame.pack_propagate(False)  # Fixed width
        
        # Title
        title = tk.Label(self.frame, text="🔍 Detected Defects", 
                        bg=config.COLOR_BG, fg="white",
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Statistics frame
        self.stats_frame = tk.Frame(self.frame, bg=config.COLOR_BG)
        self.stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.total_label = tk.Label(self.stats_frame, text="Total: 0",
                                    bg=config.COLOR_BG, fg="#00ff00",
                                    font=("Arial", 11, "bold"))
        self.total_label.pack(anchor="w")
        
        # Separator
        separator = tk.Frame(self.frame, height=2, bg="#555")
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        # Scrollable list
        list_frame = tk.Frame(self.frame, bg=config.COLOR_BG)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.defect_list = tk.Listbox(list_frame, 
                                       bg="#1e1e1e", 
                                       fg="white",
                                       font=("Consolas", 9),
                                       selectmode=tk.SINGLE,
                                       yscrollcommand=scrollbar.set)
        self.defect_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.defect_list.yview)
        
        # Clear button
        self.clear_btn = tk.Button(self.frame, text="🗑️ Clear List",
                                   bg="#f44336", fg="white",
                                   font=("Arial", 10),
                                   command=self.clear)
        self.clear_btn.pack(pady=10)
        
        # Class statistics
        self.class_stats_frame = tk.Frame(self.frame, bg=config.COLOR_BG)
        self.class_stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(self.class_stats_frame, text="By Class:",
                bg=config.COLOR_BG, fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.class_stats_text = tk.Text(self.class_stats_frame, 
                                        height=8, 
                                        bg="#1e1e1e", 
                                        fg="#00ff00",
                                        font=("Consolas", 9),
                                        state=tk.DISABLED)
        self.class_stats_text.pack(fill=tk.X, pady=5)
        
        # Internal state
        self.defect_count = 0
        self.class_counts: Dict[str, int] = {}
    
    def update_defects(self, detections: List[Dict]):
        """Update defect list with new detections
        
        Args:
            detections: List of dicts with keys: 'class', 'confidence', 'bbox'
        """
        if not detections:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        for det in detections:
            class_name = det.get('class', 'Unknown')
            conf = det.get('confidence', 0.0)
            
            # Update counts
            self.defect_count += 1
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
            
            # Add to list
            entry = f"[{timestamp}] {class_name} ({conf:.2f})"
            self.defect_list.insert(0, entry)  # Insert at top
            
            # Keep only last 100 entries
            if self.defect_list.size() > 100:
                self.defect_list.delete(tk.END)
        
        # Update UI
        self._update_stats()
        
        # Auto-scroll to top
        self.defect_list.see(0)
    
    def _update_stats(self):
        """Update statistics display"""
        # Total count
        self.total_label.config(text=f"Total: {self.defect_count}")
        
        # Class breakdown
        self.class_stats_text.config(state=tk.NORMAL)
        self.class_stats_text.delete(1.0, tk.END)
        
        if self.class_counts:
            for class_name, count in sorted(self.class_counts.items(), 
                                           key=lambda x: x[1], 
                                           reverse=True):
                percentage = (count / self.defect_count) * 100
                line = f"{class_name}: {count} ({percentage:.1f}%)\n"
                self.class_stats_text.insert(tk.END, line)
        else:
            self.class_stats_text.insert(tk.END, "No detections yet")
        
        self.class_stats_text.config(state=tk.DISABLED)
    
    def clear(self):
        """Clear all defects"""
        self.defect_list.delete(0, tk.END)
        self.defect_count = 0
        self.class_counts.clear()
        self._update_stats()