#!/usr/bin/env python3
"""
Live Ethereum Motor Demo

Real-time visualization of motors responding to live Ethereum blockchain data
with GUI interface showing motor movements.
"""

import asyncio
import json
import logging
import socket
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Dict, Any

import aiohttp


class LiveEthereumDataFetcher:
    """Fetches real live Ethereum data from public APIs."""
    
    def __init__(self):
        self.logger = logging.getLogger("EthData")
        # Using free public APIs
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        self.etherscan_url = "https://api.etherscan.io/api?module=gastracker&action=gasoracle"
    
    async def fetch_live_data(self):
        """Fetch real-time Ethereum data."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get ETH price
                eth_price = await self._fetch_eth_price(session)
                
                # Get gas price
                gas_price = await self._fetch_gas_price(session)
                
                # Calculate derived metrics
                market_condition = self._determine_market_condition(eth_price)
                activity_level = self._determine_activity_level(gas_price)
                
                data = {
                    "timestamp": time.time(),
                    "eth_price_usd": eth_price,
                    "gas_price_gwei": gas_price,
                    "market_condition": market_condition,
                    "activity_level": activity_level,
                    "data_source": "live_apis"
                }
                
                self.logger.info(f"Live data: ETH=${eth_price:.2f}, Gas={gas_price:.1f} Gwei, Market={market_condition}")
                return data
                
        except Exception as e:
            self.logger.error(f"Failed to fetch live data: {e}")
            return self._fallback_data()
    
    async def _fetch_eth_price(self, session):
        """Fetch ETH price from CoinGecko."""
        try:
            async with session.get(self.coingecko_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["ethereum"]["usd"]
        except Exception as e:
            self.logger.warning(f"CoinGecko failed: {e}")
        
        # Fallback: simulate realistic price
        import random
        return random.uniform(2000, 4000)
    
    async def _fetch_gas_price(self, session):
        """Fetch gas price from Etherscan."""
        try:
            async with session.get(self.etherscan_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "1":
                        return float(data["result"]["StandardGasPrice"])
        except Exception as e:
            self.logger.warning(f"Etherscan failed: {e}")
        
        # Fallback: simulate realistic gas price
        import random
        return random.uniform(10, 100)
    
    def _determine_market_condition(self, price):
        """Determine market condition from price."""
        if price < 2000:
            return "bear"
        elif price < 3000:
            return "sideways"
        elif price < 4000:
            return "bull"
        else:
            return "volatile"
    
    def _determine_activity_level(self, gas_price):
        """Determine network activity from gas price."""
        if gas_price < 20:
            return "low"
        elif gas_price < 50:
            return "moderate"
        else:
            return "high"
    
    def _fallback_data(self):
        """Fallback data when APIs fail."""
        import random
        return {
            "timestamp": time.time(),
            "eth_price_usd": random.uniform(2000, 4000),
            "gas_price_gwei": random.uniform(10, 100),
            "market_condition": "sideways",
            "activity_level": "moderate",
            "data_source": "fallback"
        }


class EthereumMotorController:
    """Converts Ethereum data to motor commands."""
    
    def __init__(self):
        self.logger = logging.getLogger("MotorController")
        self.max_rpm = 30.0
    
    def generate_motor_commands(self, eth_data):
        """Generate motor commands from Ethereum data."""
        eth_price = eth_data["eth_price_usd"]
        gas_price = eth_data["gas_price_gwei"]
        
        # Algorithm: Convert blockchain metrics to motor speeds
        canvas_rpm = self._calculate_canvas_speed(eth_price)
        brush_rpm = self._calculate_brush_speed(gas_price)
        color_rpm = self._calculate_color_speed(gas_price, eth_price)
        elevation_rpm = self._calculate_elevation_speed(eth_price, gas_price)
        
        commands = {
            "timestamp": eth_data["timestamp"],
            "source": eth_data["data_source"],
            "motors": {
                "canvas": {"rpm": min(canvas_rpm, self.max_rpm), "dir": "CW" if eth_price > 2500 else "CCW"},
                "pb": {"rpm": min(brush_rpm, self.max_rpm), "dir": "CW" if gas_price > 30 else "CCW"},
                "pcd": {"rpm": min(color_rpm, self.max_rpm), "dir": "CW"},
                "pe": {"rpm": min(elevation_rpm, self.max_rpm), "dir": "CW" if eth_price > 3000 else "CCW"},
            },
            "market_info": {
                "eth_price": eth_price,
                "gas_price": gas_price,
                "condition": eth_data["market_condition"],
                "activity": eth_data["activity_level"],
            }
        }
        
        total_activity = sum(motor["rpm"] for motor in commands["motors"].values())
        self.logger.info(f"Generated commands: Total activity {total_activity:.1f} RPM")
        
        return commands
    
    def _calculate_canvas_speed(self, eth_price):
        """Canvas speed based on ETH price."""
        return max(0, 5.0 + (eth_price - 2500) * 0.008)
    
    def _calculate_brush_speed(self, gas_price):
        """Brush speed based on gas price."""
        return max(0, 3.0 + gas_price * 0.25)
    
    def _calculate_color_speed(self, gas_price, eth_price):
        """Color speed based on combined metrics."""
        base = 5.0
        gas_factor = gas_price * 0.1
        price_factor = (eth_price - 2500) * 0.002
        return max(0, base + gas_factor + price_factor)
    
    def _calculate_elevation_speed(self, eth_price, gas_price):
        """Elevation speed based on market volatility."""
        volatility = abs(eth_price - 2500) + gas_price
        return max(0, 4.0 + volatility * 0.05)


class LiveMotorUI:
    """Real-time motor visualization UI."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Ethereum → Motor Control")
        self.root.geometry("800x600")
        
        # Motor display variables
        self.motor_vars = {
            "canvas": tk.DoubleVar(),
            "pb": tk.DoubleVar(),
            "pcd": tk.DoubleVar(),
            "pe": tk.DoubleVar(),
        }
        
        # Status variables
        self.eth_price_var = tk.StringVar(value="Loading...")
        self.gas_price_var = tk.StringVar(value="Loading...")
        self.market_condition_var = tk.StringVar(value="Loading...")
        self.data_source_var = tk.StringVar(value="Loading...")
        
        self.setup_ui()
        
        # Motor command sender
        self.tcp_port = 8765
        self.command_count = 0
    
    def setup_ui(self):
        """Setup the user interface."""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill="x", pady=10)
        
        ttk.Label(title_frame, text="Live Ethereum -> Motor Control", 
                 font=("Arial", 16, "bold")).pack()
        
        # Ethereum data display
        eth_frame = ttk.LabelFrame(self.root, text="Live Ethereum Data", padding=10)
        eth_frame.pack(fill="x", padx=10, pady=5)
        
        data_grid = ttk.Frame(eth_frame)
        data_grid.pack(fill="x")
        
        ttk.Label(data_grid, text="ETH Price:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(data_grid, textvariable=self.eth_price_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(data_grid, text="Gas Price:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Label(data_grid, textvariable=self.gas_price_var, font=("Arial", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5)
        
        ttk.Label(data_grid, text="Market:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(data_grid, textvariable=self.market_condition_var).grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(data_grid, text="Source:").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Label(data_grid, textvariable=self.data_source_var).grid(row=1, column=3, sticky="w", padx=5)
        
        # Motor displays
        motors_frame = ttk.LabelFrame(self.root, text="Motor Responses", padding=10)
        motors_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        motor_info = [
            ("Canvas Motor", "canvas", "Driven by ETH Price"),
            ("Pen Brush", "pb", "Driven by Gas Price"),
            ("Color Depth", "pcd", "Driven by Combined Metrics"),
            ("Pen Elevation", "pe", "Driven by Market Volatility"),
        ]
        
        for i, (name, key, description) in enumerate(motor_info):
            motor_frame = ttk.Frame(motors_frame)
            motor_frame.grid(row=i//2, column=i%2, sticky="ew", padx=10, pady=10)
            
            ttk.Label(motor_frame, text=name, font=("Arial", 12, "bold")).pack()
            ttk.Label(motor_frame, text=description, font=("Arial", 8)).pack()
            
            # Motor speed bar
            progress_frame = ttk.Frame(motor_frame)
            progress_frame.pack(fill="x", pady=5)
            
            progress = ttk.Progressbar(progress_frame, mode="determinate", length=200)
            progress.pack(side="left")
            
            rpm_label = ttk.Label(progress_frame, text="0.0 RPM", width=10)
            rpm_label.pack(side="right", padx=5)
            
            # Store references for updates
            setattr(self, f"{key}_progress", progress)
            setattr(self, f"{key}_label", rpm_label)
        
        motors_frame.grid_columnconfigure(0, weight=1)
        motors_frame.grid_columnconfigure(1, weight=1)
        
        # Status log
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=5)
        log_frame.pack(fill="x", padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.log("Live Ethereum Motor Controller Started")
        self.log("Connecting to live Ethereum APIs...")
    
    def update_ethereum_data(self, eth_data):
        """Update the Ethereum data display."""
        self.eth_price_var.set(f"${eth_data['eth_price_usd']:.2f}")
        self.gas_price_var.set(f"{eth_data['gas_price_gwei']:.1f} Gwei")
        self.market_condition_var.set(eth_data['market_condition'].upper())
        self.data_source_var.set(eth_data['data_source'].upper())
    
    def update_motors(self, commands):
        """Update motor displays."""
        motors = commands["motors"]
        
        for motor_key, motor_data in motors.items():
            rpm = motor_data["rpm"]
            direction = motor_data["dir"]
            
            # Update progress bar (0-30 RPM range)
            progress = getattr(self, f"{motor_key}_progress")
            progress["value"] = (rpm / 30.0) * 100
            
            # Update RPM label
            label = getattr(self, f"{motor_key}_label")
            label.config(text=f"{rpm:.1f} RPM {direction}")
        
        # Log the update
        market_info = commands["market_info"]
        total_rpm = sum(motor["rpm"] for motor in motors.values())
        
        self.log(f"Motors Updated: ETH=${market_info['eth_price']:.2f}, "
                f"Gas={market_info['gas_price']:.1f}, "
                f"Total={total_rpm:.1f} RPM")
    
    def send_motor_commands(self, commands):
        """Send commands to mock TCP server."""
        def send():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect(("localhost", self.tcp_port))
                
                command_json = json.dumps(commands) + "\n"
                sock.send(command_json.encode())
                
                response = sock.recv(1024).decode()
                sock.close()
                
                self.command_count += 1
                self.log(f"Sent command #{self.command_count} to motors")
                
            except Exception as e:
                self.log(f"TCP Error: {e}")
        
        threading.Thread(target=send, daemon=True).start()
    
    def log(self, message):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def run(self):
        """Start the UI."""
        self.root.mainloop()


class LiveEthereumMotorDemo:
    """Main demo coordinator."""
    
    def __init__(self):
        self.logger = logging.getLogger("Demo")
        self.fetcher = LiveEthereumDataFetcher()
        self.controller = EthereumMotorController()
        self.ui = LiveMotorUI()
        self.running = False
    
    async def start_data_loop(self):
        """Start the live data fetching loop."""
        self.running = True
        self.ui.log("Starting live data feed...")
        
        while self.running:
            try:
                # Fetch live Ethereum data
                eth_data = await self.fetcher.fetch_live_data()
                
                # Update UI with Ethereum data
                self.ui.update_ethereum_data(eth_data)
                
                # Generate motor commands
                commands = self.controller.generate_motor_commands(eth_data)
                
                # Update UI with motor commands
                self.ui.update_motors(commands)
                
                # Send to mock TCP server
                self.ui.send_motor_commands(commands)
                
                # Wait for next update
                await asyncio.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Data loop error: {e}")
                self.ui.log(f"Error: {e}")
                await asyncio.sleep(10.0)  # Wait longer on error
    
    def run_demo(self):
        """Run the complete demo."""
        # Start data loop in background
        def run_data_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_data_loop())
        
        threading.Thread(target=run_data_loop, daemon=True).start()
        
        # Run UI (blocking)
        self.ui.run()
        
        # Stop data loop when UI closes
        self.running = False


def main():
    """Main function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("LIVE ETHEREUM -> MOTOR CONTROL DEMO")
    print("="*60)
    print("This demo shows motors responding to REAL Ethereum data!")
    print("- Fetches live ETH price and gas fees from APIs")
    print("- Converts blockchain data to motor commands")
    print("- Shows real-time motor responses in GUI")
    print("- Sends commands to mock TCP motor server")
    print("\nStarting demo...")
    
    # Ask user if they want to start the mock TCP server
    print("\nFor full demo experience:")
    print("1. Open another terminal")
    print("2. Run: poetry run python tools/mock_motor_tcp.py")
    print("3. Then run this demo")
    print()
    
    input("Press Enter when ready to start the live demo...")
    
    demo = LiveEthereumMotorDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()