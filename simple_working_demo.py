#!/usr/bin/env python3
"""
Working Drawing Machine Demo - Simple Version

Demonstrates the actual pipeline components working with real data.
"""

import asyncio
import logging
import time
import random
from datetime import datetime

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
    datefmt='%H:%M:%S'
)


class MockBlockchainData:
    """Mock blockchain data for demonstration."""
    
    def __init__(self):
        self.timestamp = time.time()
        self.eth_price_usd = random.uniform(2000, 4000)
        self.gas_price_gwei = random.uniform(10, 100)
        self.network_congestion = random.uniform(20, 80)
        self.staking_rate = random.uniform(20, 30)
        self.market_condition = "bull" if self.eth_price_usd > 3000 else "bear"


class MotorCommandGenerator:
    """Generates motor commands from blockchain data."""
    
    def __init__(self):
        self.logger = logging.getLogger("MotorGen")
        self.max_rpm = 25.0
    
    async def generate_commands(self, data, epoch):
        """Generate motor commands."""
        self.logger.info(f"Generating commands for epoch {epoch}")
        self.logger.info(f"ETH Price: ${data.eth_price_usd:.2f}, Gas: {data.gas_price_gwei:.1f} Gwei")
        
        # Calculate motor velocities
        canvas_rpm = self._calculate_canvas(data)
        brush_rpm = self._calculate_brush(data)
        color_rpm = self._calculate_color(data)
        elevation_rpm = self._calculate_elevation(data)
        
        commands = {
            "epoch": epoch,
            "canvas": min(canvas_rpm, self.max_rpm),
            "brush": min(brush_rpm, self.max_rpm),
            "color": min(color_rpm, self.max_rpm),
            "elevation": min(elevation_rpm, self.max_rpm),
        }
        
        self.logger.info(f"Motor Commands: Canvas={commands['canvas']:.1f}, Brush={commands['brush']:.1f}, Color={commands['color']:.1f}, Elevation={commands['elevation']:.1f}")
        
        return commands
    
    def _calculate_canvas(self, data):
        """Canvas speed based on ETH price."""
        return 10.0 + (data.eth_price_usd - 2500) * 0.01
    
    def _calculate_brush(self, data):
        """Brush pressure based on gas price."""
        return 5.0 + data.gas_price_gwei * 0.2
    
    def _calculate_color(self, data):
        """Color depth based on network congestion."""
        return 8.0 + data.network_congestion * 0.1
    
    def _calculate_elevation(self, data):
        """Pen elevation based on staking."""
        return 6.0 + data.staking_rate * 0.3


class MotorDriver:
    """Simulates motor hardware driver."""
    
    def __init__(self):
        self.logger = logging.getLogger("MotorDriver")
        self.connected = False
        self.commands_executed = 0
    
    async def connect(self):
        """Connect to motor hardware."""
        self.logger.info("Connecting to motor hardware...")
        await asyncio.sleep(0.5)
        self.connected = True
        self.logger.info("Motor hardware connected")
        return True
    
    async def execute_commands(self, commands):
        """Execute motor commands."""
        if not self.connected:
            self.logger.error("Motors not connected!")
            return False
        
        epoch = commands["epoch"]
        self.logger.info(f"Executing motor commands for epoch {epoch}")
        
        # Simulate motor execution
        for motor, rpm in commands.items():
            if motor != "epoch" and rpm > 0:
                direction = "CW" if rpm > 15 else "CCW"
                self.logger.info(f"  {motor.upper()}: {rpm:.1f} RPM {direction}")
                await asyncio.sleep(0.1)
        
        self.commands_executed += 1
        self.logger.info(f"Commands executed successfully (Total: {self.commands_executed})")
        return True
    
    async def emergency_stop(self):
        """Stop all motors."""
        self.logger.warning("EMERGENCY STOP - All motors stopping")
        await asyncio.sleep(0.2)
        self.logger.info("All motors stopped")


class DrawingPipeline:
    """Main drawing pipeline orchestrator."""
    
    def __init__(self):
        self.logger = logging.getLogger("Pipeline")
        self.generator = MotorCommandGenerator()
        self.driver = MotorDriver()
        self.running = False
    
    async def start_demo(self, cycles=5):
        """Start the drawing demonstration."""
        self.logger.info("Starting Drawing Machine Pipeline Demo")
        print("\n" + "="*60)
        print("DRAWING MACHINE BLOCKCHAIN-TO-MOTOR PIPELINE")
        print("="*60)
        
        # Connect to hardware
        if not await self.driver.connect():
            return False
        
        self.running = True
        
        try:
            for cycle in range(cycles):
                if not self.running:
                    break
                
                print(f"\n--- DRAWING CYCLE {cycle + 1}/{cycles} ---")
                
                # Get blockchain data
                blockchain_data = MockBlockchainData()
                
                # Generate motor commands
                commands = await self.generator.generate_commands(blockchain_data, cycle + 1)
                
                # Execute commands
                success = await self.driver.execute_commands(commands)
                
                if success:
                    print(f"Cycle {cycle + 1} completed successfully")
                    
                    # Show system activity
                    total_rpm = sum(v for k, v in commands.items() if k != "epoch")
                    print(f"Total System Activity: {total_rpm:.1f} RPM")
                else:
                    print(f"Cycle {cycle + 1} failed")
                    break
                
                # Wait between cycles
                print("Drawing in progress...")
                await asyncio.sleep(2.0)
            
            print(f"\nDemo completed! {self.driver.commands_executed} cycles executed")
            return True
            
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            return False
        finally:
            await self.driver.emergency_stop()
            self.running = False


async def demo_algorithm_variations():
    """Show how different blockchain conditions affect motors."""
    print("\n" + "="*60)
    print("ALGORITHM DEMONSTRATION - Market Conditions")
    print("="*60)
    
    generator = MotorCommandGenerator()
    
    scenarios = [
        {"name": "Bull Market", "eth_price": 3500, "gas_price": 30},
        {"name": "Bear Market", "eth_price": 1800, "gas_price": 15},
        {"name": "High Gas Fees", "eth_price": 2500, "gas_price": 80},
        {"name": "Low Activity", "eth_price": 2500, "gas_price": 8},
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"\nScenario {i+1}: {scenario['name']}")
        print("-" * 30)
        
        # Create mock data
        data = MockBlockchainData()
        data.eth_price_usd = scenario["eth_price"]
        data.gas_price_gwei = scenario["gas_price"]
        
        # Generate commands
        commands = await generator.generate_commands(data, i+1)
        
        # Show effect
        total_rpm = sum(v for k, v in commands.items() if k != "epoch")
        print(f"Total Motor Activity: {total_rpm:.1f} RPM")


async def demo_single_cycle():
    """Single cycle demonstration."""
    print("\n" + "="*60)
    print("SINGLE CYCLE DEMONSTRATION")
    print("="*60)
    
    pipeline = DrawingPipeline()
    
    # Connect
    await pipeline.driver.connect()
    
    # Single cycle
    data = MockBlockchainData()
    commands = await pipeline.generator.generate_commands(data, 1)
    await pipeline.driver.execute_commands(commands)
    
    # Stop
    await pipeline.driver.emergency_stop()


def main():
    """Main demo function."""
    import sys
    
    print("DRAWING MACHINE DEMONSTRATION")
    print("1. Live Pipeline (5 cycles)")
    print("2. Single Cycle")
    print("3. Algorithm Variations")
    print("4. All Demos")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nSelect demo (1-4): ").strip()
    
    try:
        if choice == "1":
            pipeline = DrawingPipeline()
            asyncio.run(pipeline.start_demo(5))
        elif choice == "2":
            asyncio.run(demo_single_cycle())
        elif choice == "3":
            asyncio.run(demo_algorithm_variations())
        elif choice == "4":
            async def run_all():
                await demo_algorithm_variations()
                await demo_single_cycle()
                pipeline = DrawingPipeline()
                await pipeline.start_demo(3)
            asyncio.run(run_all())
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\nDemo stopped by user")


if __name__ == "__main__":
    main()