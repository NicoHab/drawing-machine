import tkinter as tk
from tkinter import ttk
import asyncio
import json
import time
import threading

class ControlPanelGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drawing Machine Control Panel")
        self.root.geometry("600x500")
        
        # Motor control variables
        self.motor_speeds = {
            "canvas": tk.DoubleVar(value=0.0),
            "pb": tk.DoubleVar(value=0.0),
            "pcd": tk.DoubleVar(value=0.0),
            "pe": tk.DoubleVar(value=0.0)
        }
        
        self.motor_directions = {
            "canvas": tk.StringVar(value="CW"),
            "pb": tk.StringVar(value="CW"),
            "pcd": tk.StringVar(value="CW"),
            "pe": tk.StringVar(value="CW")
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = ttk.Label(self.root, text="Drawing Machine Control Panel", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Motor controls frame
        motors_frame = ttk.LabelFrame(self.root, text="Motor Controls", padding=10)
        motors_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        motor_names = ["Canvas", "Motor PB", "Motor PCD", "Motor PE"]
        motor_keys = ["canvas", "pb", "pcd", "pe"]
        
        for i, (name, key) in enumerate(zip(motor_names, motor_keys)):
            # Motor frame
            motor_frame = ttk.LabelFrame(motors_frame, text=name, padding=5)
            motor_frame.grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)
            
            # Speed control
            ttk.Label(motor_frame, text="Speed (RPM):").pack()
            speed_scale = ttk.Scale(motor_frame, from_=0, to=35, 
                                  variable=self.motor_speeds[key],
                                  orient="horizontal", length=200)
            speed_scale.pack(pady=5)
            
            # Speed display
            speed_label = ttk.Label(motor_frame, text="0.0 RPM")
            speed_label.pack()
            
            # Update speed label when changed
            def update_label(val, label=speed_label, var=self.motor_speeds[key]):
                label.config(text=f"{var.get():.1f} RPM")
            
            self.motor_speeds[key].trace('w', lambda *args, f=update_label: f(None))
            
            # Direction control
            dir_frame = ttk.Frame(motor_frame)
            dir_frame.pack(pady=5)
            
            ttk.Radiobutton(dir_frame, text="CW", variable=self.motor_directions[key],
                           value="CW").pack(side="left", padx=5)
            ttk.Radiobutton(dir_frame, text="CCW", variable=self.motor_directions[key],
                           value="CCW").pack(side="left", padx=5)
        
        # Configure grid
        motors_frame.grid_columnconfigure(0, weight=1)
        motors_frame.grid_columnconfigure(1, weight=1)
        
        # Control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Send Command", 
                  command=self.send_command).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Stop All", 
                  command=self.stop_all).pack(side="left", padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.root, textvariable=self.status_var)
        status_label.pack(pady=5)
    
    def send_command(self):
        # This will send commands to our TCP motor controller
        command = {
            "timestamp": time.time(),
            "epoch": int(time.time()) % 1000,
            "motors": {
                key: {
                    "rpm": var.get(),
                    "dir": self.motor_directions[key].get()
                }
                for key, var in self.motor_speeds.items()
            }
        }
        
        # For now, just show the command would be sent
        self.status_var.set(f"Command sent: Canvas={command['motors']['canvas']['rpm']:.1f}RPM")
        print(f"Would send: {command}")
    
    def stop_all(self):
        for var in self.motor_speeds.values():
            var.set(0.0)
        for var in self.motor_directions.values():
            var.set("CW")
        self.status_var.set("All motors stopped")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ControlPanelGUI()
    app.run()