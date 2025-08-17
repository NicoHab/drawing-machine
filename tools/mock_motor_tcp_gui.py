#!/usr/bin/env python3
"""
Mock Motor TCP Server with GUI

Visual TCP server that displays real-time motor states and commands 
received from the manual control system.
"""

import asyncio
import json
import logging
import math
import time
import tkinter as tk
from tkinter import ttk
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MotorState:
    """State of a single motor."""
    velocity_rpm: float = 0.0
    direction: str = "CW"
    last_update: float = 0.0
    total_commands: int = 0


class MotorVisualization:
    """Visual representation of a motor."""
    
    def __init__(self, canvas, x, y, radius, name, color):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.name = name
        self.color = color
        self.angle = 0
        self.velocity = 0
        self.direction = "CW"
        
        # Draw motor base circle
        self.base = canvas.create_oval(
            x - radius, y - radius, 
            x + radius, y + radius,
            fill="lightgray", outline="black", width=2
        )
        
        # Draw motor pointer/arm
        self.pointer = canvas.create_line(
            x, y, x + radius - 5, y,
            fill=color, width=4, arrow=tk.LAST
        )
        
        # Motor name label
        self.name_label = canvas.create_text(
            x, y + radius + 15,
            text=name, font=("Arial", 10, "bold")
        )
        
        # RPM label
        self.rpm_label = canvas.create_text(
            x, y + radius + 30,
            text="0.0 RPM", font=("Arial", 8)
        )
        
        # Direction label
        self.direction_label = canvas.create_text(
            x, y + radius + 45,
            text="CW", font=("Arial", 8)
        )
    
    def update(self, velocity_rpm, direction):
        """Update motor visualization."""
        self.velocity = velocity_rpm
        self.direction = direction
        
        # Update rotation based on velocity and direction
        rotation_speed = abs(velocity_rpm) * 0.1  # Scale down for visual effect
        if direction == "CCW":
            rotation_speed = -rotation_speed
        
        self.angle += rotation_speed
        if self.angle >= 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360
        
        # Calculate new pointer position
        rad = math.radians(self.angle)
        end_x = self.x + (self.radius - 5) * math.cos(rad)
        end_y = self.y + (self.radius - 5) * math.sin(rad)
        
        # Update pointer
        self.canvas.coords(self.pointer, self.x, self.y, end_x, end_y)
        
        # Update color based on activity
        activity_color = self.color
        if abs(velocity_rpm) > 50:
            activity_color = "red"
        elif abs(velocity_rpm) > 25:
            activity_color = "orange"
        elif abs(velocity_rpm) > 0:
            activity_color = "green"
        else:
            activity_color = "gray"
        
        self.canvas.itemconfig(self.pointer, fill=activity_color)
        
        # Update labels
        self.canvas.itemconfig(self.rpm_label, text=f"{velocity_rpm:.1f} RPM")
        self.canvas.itemconfig(self.direction_label, text=direction)


class MockMotorTCPServerGUI:
    """Mock motor TCP server with real-time GUI visualization."""
    
    def __init__(self, host="localhost", port=8767):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Motor states
        self.motors = {
            "motor_canvas": MotorState(),
            "motor_pb": MotorState(), 
            "motor_pcd": MotorState(),
            "motor_pe": MotorState(),
        }
        
        # Server stats
        self.server_start_time = time.time()
        self.total_connections = 0
        self.total_commands = 0
        self.active_connections = 0
        
        # GUI components
        self.root = None
        self.canvas = None
        self.motor_visualizations = {}
        self.info_labels = {}
        
        # Animation
        self.animation_running = False
        
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root = tk.Tk()
        self.root.title("Mock Motor TCP Server - Real-time Visualization")
        self.root.geometry("800x600")
        self.root.configure(bg="white")
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(header_frame, text="Drawing Machine - Motor TCP Server", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text=f"Listening on {self.host}:{self.port}", 
                 font=("Arial", 10)).pack()
        
        # Server stats frame
        stats_frame = ttk.LabelFrame(self.root, text="Server Statistics", padding=5)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x")
        
        # Stats labels
        self.info_labels = {
            "uptime": ttk.Label(stats_grid, text="Uptime: 0s"),
            "connections": ttk.Label(stats_grid, text="Total Connections: 0"),
            "active": ttk.Label(stats_grid, text="Active Connections: 0"),
            "commands": ttk.Label(stats_grid, text="Total Commands: 0"),
            "last_command": ttk.Label(stats_grid, text="Last Command: None")
        }
        
        # Arrange stats in grid
        row = 0
        for i, (key, label) in enumerate(self.info_labels.items()):
            label.grid(row=row, column=i % 3, sticky="w", padx=10, pady=2)
            if (i + 1) % 3 == 0:
                row += 1
        
        # Motor visualization canvas
        canvas_frame = ttk.LabelFrame(self.root, text="Motor Visualizations", padding=10)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", height=300)
        self.canvas.pack(fill="both", expand=True)
        
        # Create motor visualizations
        motor_configs = [
            ("motor_canvas", "Canvas Motor", "blue", 150, 150),
            ("motor_pb", "Pen Brush", "green", 450, 150),
            ("motor_pcd", "Color Depth", "purple", 150, 300),
            ("motor_pe", "Pen Elevation", "orange", 450, 300),
        ]
        
        for motor_key, name, color, x, y in motor_configs:
            self.motor_visualizations[motor_key] = MotorVisualization(
                self.canvas, x, y, 40, name, color
            )
        
        # Command log frame
        log_frame = ttk.LabelFrame(self.root, text="Recent Commands", padding=5)
        log_frame.pack(fill="x", padx=10, pady=5)
        
        # Command log text area
        self.log_text = tk.Text(log_frame, height=6, font=("Consolas", 8))
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # Control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset Stats", command=self.reset_stats).pack(side="left", padx=5)
        
        # Start animation
        self.animation_running = True
        self.animate_motors()
        
        self.log_message("Motor TCP Server GUI started")
        self.log_message(f"Waiting for connections on {self.host}:{self.port}")
    
    def animate_motors(self):
        """Animate motor visualizations."""
        if not self.animation_running:
            return
        
        # Update each motor visualization
        for motor_key, visualization in self.motor_visualizations.items():
            motor_state = self.motors[motor_key]
            visualization.update(motor_state.velocity_rpm, motor_state.direction)
        
        # Update server statistics
        self.update_stats()
        
        # Schedule next animation frame
        if self.root:
            self.root.after(50, self.animate_motors)  # 20 FPS
    
    def update_stats(self):
        """Update server statistics display."""
        uptime = int(time.time() - self.server_start_time)
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        self.info_labels["uptime"].config(text=f"Uptime: {uptime_str}")
        self.info_labels["connections"].config(text=f"Total Connections: {self.total_connections}")
        self.info_labels["active"].config(text=f"Active Connections: {self.active_connections}")
        self.info_labels["commands"].config(text=f"Total Commands: {self.total_commands}")
    
    def log_message(self, message):
        """Add message to command log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        # Limit log size
        lines = self.log_text.get("1.0", tk.END).count("\n")
        if lines > 100:
            self.log_text.delete("1.0", "10.0")
    
    def clear_log(self):
        """Clear the command log."""
        self.log_text.delete("1.0", tk.END)
        self.log_message("Log cleared")
    
    def reset_stats(self):
        """Reset server statistics."""
        self.server_start_time = time.time()
        self.total_connections = 0
        self.total_commands = 0
        self.log_message("Statistics reset")
    
    async def handle_client(self, reader, writer):
        """Handle TCP client connection."""
        client_addr = writer.get_extra_info('peername')
        self.total_connections += 1
        self.active_connections += 1
        
        self.log_message(f"Client connected: {client_addr}")
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    command = json.loads(data.decode().strip())
                    await self.process_command(command, client_addr)
                    
                    # Send response
                    response = {
                        "status": "ACK",
                        "timestamp": time.time(),
                        "command_id": self.total_commands
                    }
                    
                    response_data = json.dumps(response) + "\n"
                    writer.write(response_data.encode())
                    await writer.drain()
                    
                except json.JSONDecodeError as e:
                    self.log_message(f"Invalid JSON from {client_addr}: {e}")
                except Exception as e:
                    self.log_message(f"Error processing command from {client_addr}: {e}")
        
        except Exception as e:
            self.log_message(f"Connection error with {client_addr}: {e}")
        finally:
            self.active_connections -= 1
            self.log_message(f"Client disconnected: {client_addr}")
            writer.close()
            await writer.wait_closed()
    
    async def process_command(self, command, client_addr):
        """Process incoming motor command."""
        self.total_commands += 1
        
        # Handle different command formats
        if "motor_name" in command:
            # Single motor command from manual control
            motor_name = command["motor_name"]
            velocity_rpm = command.get("velocity_rpm", 0)
            direction = command.get("direction", "CW")
            
            if motor_name in self.motors:
                self.motors[motor_name].velocity_rpm = velocity_rpm
                self.motors[motor_name].direction = direction
                self.motors[motor_name].last_update = time.time()
                self.motors[motor_name].total_commands += 1
                
                self.log_message(f"Motor {motor_name}: {velocity_rpm:.1f} RPM {direction}")
                self.info_labels["last_command"].config(
                    text=f"Last: {motor_name} -> {velocity_rpm:.1f} RPM {direction}"
                )
        
        elif "motors" in command:
            # Multiple motor command
            for motor_name, motor_cmd in command["motors"].items():
                if motor_name in self.motors:
                    rpm = motor_cmd.get("rpm", 0)
                    direction = motor_cmd.get("dir", "CW")
                    
                    self.motors[motor_name].velocity_rpm = rpm
                    self.motors[motor_name].direction = direction
                    self.motors[motor_name].last_update = time.time()
                    self.motors[motor_name].total_commands += 1
            
            motor_summary = ", ".join([
                f"{name}: {self.motors[name].velocity_rpm:.1f}"
                for name in command["motors"].keys()
                if name in self.motors
            ])
            self.log_message(f"Multi-motor: {motor_summary}")
            self.info_labels["last_command"].config(text=f"Last: Multi-motor update")
        
        else:
            self.log_message(f"Unknown command format: {command}")
    
    async def start_server(self):
        """Start the TCP server."""
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        
        self.log_message(f"TCP server started on {self.host}:{self.port}")
        
        async with server:
            await server.serve_forever()
    
    def run(self):
        """Run the GUI and TCP server."""
        # Setup GUI
        self.setup_gui()
        
        # Start TCP server in background thread
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start_server())
            except Exception as e:
                self.log_message(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Start GUI main loop
        try:
            self.root.mainloop()
        finally:
            self.animation_running = False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Starting Mock Motor TCP Server with GUI...")
    server = MockMotorTCPServerGUI()
    server.run()