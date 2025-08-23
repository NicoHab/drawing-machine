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
        
        # Motor data label (shows blockchain data driving this motor)
        self.data_label = canvas.create_text(
            x, y + radius + 30,
            text="No data", font=("Arial", 7), width=120
        )
        
        # RPM label
        self.rpm_label = canvas.create_text(
            x, y + radius + 45,
            text="0.0 RPM CW", font=("Arial", 9, "bold")
        )
    
    def update(self, velocity_rpm, direction, blockchain_data=None):
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
        
        # Update labels with signed RPM (negative for CCW)
        rpm_display = f"{'-' if direction == 'CCW' else ''}{velocity_rpm:.1f} RPM"
        self.canvas.itemconfig(self.rpm_label, text=rpm_display)
        
        # Update blockchain data label if available
        if blockchain_data:
            data_text = self.get_motor_data_text(blockchain_data)
            self.canvas.itemconfig(self.data_label, text=data_text)
    
    def get_motor_data_text(self, blockchain_data):
        """Get blockchain data text for this specific motor."""
        if self.name == "Canvas":
            eth_price = blockchain_data.get("eth_price_usd", 0)
            return f"ETH: ${eth_price:.2f}"
        elif self.name == "PB":
            gas_price = blockchain_data.get("gas_price_gwei", 0)
            return f"Gas: {gas_price:.3f} gwei"
        elif self.name == "PCD":
            blob_util = blockchain_data.get("blob_space_utilization_percent", 0)
            return f"Blob: {blob_util:.1f}%"
        elif self.name == "PE":
            block_full = blockchain_data.get("block_fullness_percent", 0)
            return f"Block: {block_full:.1f}%"
        return "No data"


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
        self.processed_blocks = 0
        self.manual_commands = 0
        self.active_connections = 0
        
        # Current blockchain data for display
        self.last_blockchain_data = None
        self.current_epoch = None
        self.current_block = None
        self.current_eth_price = None
        
        # Drawing mode tracking
        self.current_drawing_mode = "UNKNOWN"
        self.data_source = "Unknown"
        
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
        
        # Drawing mode indicator
        self.mode_label = ttk.Label(header_frame, text="🎨 DRAWING MODE: UNKNOWN", 
                                   font=("Arial", 12, "bold"))
        self.mode_label.pack(pady=5)
        
        # Server stats frame
        stats_frame = ttk.LabelFrame(self.root, text="Server Statistics", padding=5)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x")
        
        # Stats labels - updated to show mode-aware format
        self.info_labels = {
            "current_epoch": ttk.Label(stats_grid, text="Current Epoch: N/A", font=("Arial", 10, "bold")),
            "current_block": ttk.Label(stats_grid, text="Current Block: N/A", font=("Arial", 10, "bold")),
            "current_eth": ttk.Label(stats_grid, text="Current ETH Price: $0.00", font=("Arial", 10, "bold")),
            "data_source_session": ttk.Label(stats_grid, text="Data Source: Unknown  Session: N/A"),
            "uptime": ttk.Label(stats_grid, text="Uptime: 0s"),
            "total_commands": ttk.Label(stats_grid, text="Total: 0 (0 blocks, 0 manual)")
        }
        
        # Arrange stats in grid with mode-aware layout
        # Row 0: Epoch and Block
        self.info_labels["current_epoch"].grid(row=0, column=0, sticky="w", padx=10, pady=2)
        self.info_labels["current_block"].grid(row=0, column=1, sticky="w", padx=10, pady=2)
        
        # Row 1: ETH Price (spans across)
        self.info_labels["current_eth"].grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        # Row 2: Data Source and Session (spans across)
        self.info_labels["data_source_session"].grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        # Row 3: Uptime and Total Commands
        self.info_labels["uptime"].grid(row=3, column=0, sticky="w", padx=10, pady=2)
        self.info_labels["total_commands"].grid(row=3, column=1, sticky="w", padx=10, pady=2)
        
        # Motor visualization canvas
        canvas_frame = ttk.LabelFrame(self.root, text="Motor Visualizations", padding=10)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", height=300)
        self.canvas.pack(fill="both", expand=True)
        
        # Create motor visualizations
        motor_configs = [
            ("motor_canvas", "Canvas", "blue", 150, 150),
            ("motor_pb", "PB", "green", 450, 150),
            ("motor_pcd", "PCD", "purple", 150, 300),
            ("motor_pe", "PE", "orange", 450, 300),
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
        
        # Update each motor visualization with current blockchain data
        current_blockchain_data = getattr(self, 'last_blockchain_data', None)
        for motor_key, visualization in self.motor_visualizations.items():
            motor_state = self.motors[motor_key]
            visualization.update(motor_state.velocity_rpm, motor_state.direction, current_blockchain_data)
        
        # Update mode display if it exists
        if hasattr(self, 'mode_label'):
            self.mode_label.config(text=f"🎨 DRAWING MODE: {self.current_drawing_mode}")
        
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
        
        # Update total commands (blocks + manual)
        total_commands = self.processed_blocks + self.manual_commands
        self.info_labels["total_commands"].config(
            text=f"Total: {total_commands} ({self.processed_blocks} blocks, {self.manual_commands} manual)"
        )
        
        # Update data source and session info
        self.info_labels["data_source_session"].config(
            text=f"Data Source: {self.data_source}  Session: {self.current_drawing_mode}"
        )
        
        # Update blockchain-specific stats (always show current data)
        if self.current_epoch is not None:
            self.info_labels["current_epoch"].config(text=f"Current Epoch: {self.current_epoch}")
        else:
            self.info_labels["current_epoch"].config(text="Current Epoch: N/A")
            
        if self.current_block is not None:
            self.info_labels["current_block"].config(text=f"Current Block: {self.current_block}")
        else:
            self.info_labels["current_block"].config(text="Current Block: N/A")
            
        if self.current_eth_price is not None:
            self.info_labels["current_eth"].config(text=f"Current ETH Price: ${self.current_eth_price:.2f}")
        else:
            self.info_labels["current_eth"].config(text="Current ETH Price: N/A")
    
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
        self.processed_blocks = 0
        self.manual_commands = 0
        self.current_epoch = None
        self.current_block = None
        self.current_eth_price = None
        self.current_drawing_mode = "UNKNOWN"
        self.data_source = "Unknown"
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
                        "command_id": self.processed_blocks if "blockchain_data" in command else self.total_connections
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
    
    def get_motor_display_name(self, motor_name):
        """Get display name for motor."""
        name_map = {
            'motor_canvas': 'Canvas',
            'motor_pb': 'PB',
            'motor_pcd': 'PCD',
            'motor_pe': 'PE'
        }
        return name_map.get(motor_name, motor_name)
    
    def detect_drawing_mode(self, command):
        """Detect drawing mode from command structure."""
        if "blockchain_data" in command:
            if "manual_override" in command:
                return "HYBRID"
            else:
                return "AUTO-BLOCKCHAIN"
        elif "motor_name" in command:
            return "MANUAL"
        elif "session_replay" in command:
            return "OFFLINE-REPLAY"
        else:
            return "UNKNOWN"
    
    async def process_command(self, command, client_addr):
        """Process incoming motor command."""
        # Detect and update drawing mode
        self.current_drawing_mode = self.detect_drawing_mode(command)
        
        # Track command types separately
        if "blockchain_data" in command:
            self.processed_blocks += 1
            self.data_source = "Live Blockchain"
        elif "motor_name" in command:
            self.manual_commands += 1
            self.data_source = "Manual Control"
        else:
            # Unknown command type
            self.data_source = "Unknown"
        
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
                
                motor_display = self.get_motor_display_name(motor_name)
                rpm_display = f"{'-' if direction == 'CCW' else ''}{velocity_rpm:.1f}"
                self.log_message(f"{motor_display}: {rpm_display} RPM")
                self.info_labels["last_command"].config(
                    text=f"Last: {motor_name} -> {velocity_rpm:.1f} RPM {direction}"
                )
        
        elif "motors" in command:
            # Multiple motor command with optional blockchain data
            for motor_name, motor_cmd in command["motors"].items():
                if motor_name in self.motors:
                    rpm = motor_cmd.get("rpm", 0)
                    direction = motor_cmd.get("dir", "CW")
                    
                    self.motors[motor_name].velocity_rpm = rpm
                    self.motors[motor_name].direction = direction
                    self.motors[motor_name].last_update = time.time()
                    self.motors[motor_name].total_commands += 1
            
            # Create motor summary
            motor_summary = ", ".join([
                f"{name}: {self.motors[name].velocity_rpm:.1f}"
                for name in command["motors"].keys()
                if name in self.motors
            ])
            
            # Include blockchain data if available
            if "blockchain_data" in command:
                blockchain_data = command["blockchain_data"]
                self.last_blockchain_data = blockchain_data  # Store for motor visualizations
                
                eth_price = blockchain_data.get("eth_price_usd", 0)
                gas_price = blockchain_data.get("gas_price_gwei", 0)
                blob_util = blockchain_data.get("blob_space_utilization_percent", 0)
                block_full = blockchain_data.get("block_fullness_percent", 0)
                epoch = blockchain_data.get("epoch", "N/A")
                block_number = blockchain_data.get("block_number", "N/A")
                
                # Get data sources for enhanced logging
                data_sources = blockchain_data.get("data_sources", {})
                eth_source = data_sources.get("eth_price_source", "unknown")
                gas_source = data_sources.get("gas_price_source", "unknown")
                epoch_source = data_sources.get("epoch_source", "unknown")
                block_source = data_sources.get("block_number_source", "unknown")
                
                # Update current blockchain data for server statistics
                self.current_epoch = epoch
                self.current_block = block_number if block_number != "N/A" else None
                self.current_eth_price = eth_price
                
                # Update drawing mode display
                if hasattr(self, 'mode_label'):
                    self.mode_label.config(text=f"🎨 DRAWING MODE: {self.current_drawing_mode}")
                
                # Enhanced logging format with data sources and block number
                block_display = block_number if block_number != "N/A" else "N/A"
                self.log_message(f"═══ EPOCH {epoch} - BLOCK {block_display} ═══")
                
                # Canvas motor
                canvas_rpm = self.motors.get('motor_canvas', MotorState()).velocity_rpm
                canvas_dir = self.motors.get('motor_canvas', MotorState()).direction
                canvas_display = f"{'-' if canvas_dir == 'CCW' else ''}{canvas_rpm:.1f}"
                self.log_message(f"Canvas - ETH Price: ${eth_price:.2f} ({eth_source}) → {canvas_display} RPM")
                
                # PB motor
                pb_rpm = self.motors.get('motor_pb', MotorState()).velocity_rpm
                pb_dir = self.motors.get('motor_pb', MotorState()).direction
                pb_display = f"{'-' if pb_dir == 'CCW' else ''}{pb_rpm:.1f}"
                self.log_message(f"PB - Gas: {gas_price:.3f} gwei ({gas_source}) → {pb_display} RPM")
                
                # PCD motor
                pcd_rpm = self.motors.get('motor_pcd', MotorState()).velocity_rpm
                pcd_dir = self.motors.get('motor_pcd', MotorState()).direction
                pcd_display = f"{'-' if pcd_dir == 'CCW' else ''}{pcd_rpm:.1f}"
                blob_source = data_sources.get("blob_util_source", "estimated")
                self.log_message(f"PCD - Blob Utilization: {blob_util:.1f}% ({blob_source}) → {pcd_display} RPM")
                
                # PE motor
                pe_rpm = self.motors.get('motor_pe', MotorState()).velocity_rpm
                pe_dir = self.motors.get('motor_pe', MotorState()).direction
                pe_display = f"{'-' if pe_dir == 'CCW' else ''}{pe_rpm:.1f}"
                fullness_source = data_sources.get("block_fullness_source", "fallback")
                self.log_message(f"PE - Block Fullness: {block_full:.1f}% ({fullness_source}) → {pe_display} RPM")
            else:
                # Regular multi-motor command without blockchain data
                self.log_message(f"Multi-motor: {motor_summary}")
                # Don't reset blockchain stats for non-blockchain commands
        
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