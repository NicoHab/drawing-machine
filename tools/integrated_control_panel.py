import tkinter as tk
from tkinter import ttk
import socket
import json
import time
import threading

class SimpleControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Motor Control Panel")
        self.root.geometry("600x400")
        
        self.motor_speeds = {
            "canvas": tk.DoubleVar(value=0.0),
            "pb": tk.DoubleVar(value=0.0),
            "pcd": tk.DoubleVar(value=0.0),
            "pe": tk.DoubleVar(value=0.0)
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        ttk.Label(self.root, text="Motor Control Panel", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        motors_frame = ttk.LabelFrame(self.root, text="Motors", padding=10)
        motors_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        motor_names = ["Canvas", "PB", "PCD", "PE"]
        motor_keys = ["canvas", "pb", "pcd", "pe"]
        
        for i, (name, key) in enumerate(zip(motor_names, motor_keys)):
            frame = ttk.Frame(motors_frame)
            frame.grid(row=i//2, column=i%2, sticky="ew", padx=10, pady=5)
            
            ttk.Label(frame, text=f"{name}:").pack()
            
            scale = ttk.Scale(frame, from_=0, to=35, variable=self.motor_speeds[key], 
                            orient="horizontal", length=150)
            scale.pack()
            
            label = ttk.Label(frame, text="0.0 RPM")
            label.pack()
            
            def make_updater(lbl, var):
                def update(*args):
                    lbl.config(text=f"{var.get():.1f} RPM")
                return update
            
            self.motor_speeds[key].trace('w', make_updater(label, self.motor_speeds[key]))
        
        motors_frame.grid_columnconfigure(0, weight=1)
        motors_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Send Command", 
                  command=self.send_command).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Stop All", 
                  command=self.stop_all).pack(side="left", padx=5)
        
        self.status_text = tk.Text(self.root, height=6)
        self.status_text.pack(fill="x", padx=10, pady=5)
        
        self.log("Control Panel ready")
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def send_command(self):
        command = {
            "timestamp": time.time(),
            "epoch": 1,
            "motors": {
                key: {"rpm": var.get(), "dir": "CW"}
                for key, var in self.motor_speeds.items()
            }
        }
        
        def send():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect(('localhost', 8765))
                
                cmd_str = json.dumps(command) + "\n"
                sock.send(cmd_str.encode())
                
                response_data = sock.recv(1024)
                response = json.loads(response_data.decode().strip())
                
                sock.close()
                
                canvas_rpm = response.get('motors', {}).get('canvas', {}).get('rpm', 0)
                self.root.after(0, lambda: self.log(f"✅ Success! Canvas: {canvas_rpm} RPM"))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.log(f"❌ Error: {error_msg}"))
        
        thread = threading.Thread(target=send)
        thread.daemon = True
        thread.start()
    
    def stop_all(self):
        for var in self.motor_speeds.values():
            var.set(0.0)
        self.send_command()
        self.log("🛑 All motors stopped")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleControlPanel()
    app.run()