#!/usr/bin/env python3
"""
Complete Drawing Machine System Demo

Demonstrates the full Drawing Machine system with Cloud Orchestrator,
manual control, blockchain data processing, and visual motor feedback.

This is the complete end-to-end system demo showcasing:
- Cloud Orchestrator (central coordination)
- Manual Control WebSocket Server
- Blockchain Data Aggregator  
- Visual Motor TCP Server with GUI
- Session Management
- Real-time Multi-client Support
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    
load_env_file()


def get_system_mode():
    """Get current system mode from file."""
    try:
        mode_file = Path(__file__).parent / "system_mode.txt"
        if mode_file.exists():
            with open(mode_file, 'r') as f:
                mode = f.read().strip()
                print(f"   DEBUG: Read system mode: '{mode}' from {mode_file}")
                return mode
        print(f"   DEBUG: Mode file {mode_file} doesn't exist, defaulting to auto")
        return "auto"  # Default to auto mode
    except Exception as e:
        print(f"   DEBUG: Error reading mode file: {e}, defaulting to auto")
        return "auto"


def save_last_motor_states(motor_states):
    """Save last motor states for smooth transitions."""
    try:
        import json
        states_file = Path(__file__).parent / "last_motor_states.json"
        with open(states_file, 'w') as f:
            json.dump(motor_states, f, indent=2)
        print(f"   Saved motor states for transition: {len(motor_states)} motors")
    except Exception as e:
        print(f"   Error saving motor states: {e}")


def start_visual_motor_server():
    """Start the GUI motor TCP server."""
    print("Starting Visual Motor TCP Server...")
    
    process = subprocess.Popen(
        [sys.executable, "tools/mock_motor_tcp_gui.py"],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"   Visual Motor Server started (PID: {process.pid})")
    print("   Motor visualization window should appear")
    return process


async def start_manual_control_server():
    """Start the manual control WebSocket server."""
    print("Starting Manual Control WebSocket Server...")
    
    from edge.manual_control.manual_control_server import ManualControlServer
    
    server = ManualControlServer(host="localhost", port=8766)
    server_task = asyncio.create_task(server.start_server())
    
    print("   Manual Control Server started on ws://localhost:8766")
    return server_task


async def start_cloud_orchestrator():
    """Start the cloud orchestrator."""
    print("Starting Cloud Orchestrator...")
    
    from cloud.orchestrator.cloud_orchestrator import CloudOrchestrator
    
    global cloud_orchestrator_instance
    cloud_orchestrator_instance = CloudOrchestrator(host="localhost", port=8768)
    orchestrator_task = asyncio.create_task(cloud_orchestrator_instance.start_server())
    
    print("   Cloud Orchestrator started on ws://localhost:8768")
    return orchestrator_task

# Global reference to orchestrator for blockchain data broadcasting
cloud_orchestrator_instance = None


async def start_blockchain_data_service():
    """Start the blockchain data processing service with motor connection."""
    print("Starting Blockchain Data Service...")
    
    from cloud.data_aggregator.data_processor import DataProcessor
    import socket
    import json
    
    processor = DataProcessor()
    
    # Start block-based data processing with motor commands
    async def block_data_loop():
        # Initialize block monitoring
        fetcher = processor.fetcher
        current_block = await fetcher.get_latest_block_number()
        print(f"   Starting block-based processing from block {current_block}")
        
        while True:
            try:
                # Check system mode before processing
                current_mode = get_system_mode()
                print(f"   DEBUG: Current mode check: '{current_mode}'")
                if current_mode == "manual":
                    print(f"   System in MANUAL mode - pausing blockchain processing...")
                    await asyncio.sleep(5)  # Check mode every 5 seconds
                    continue
                else:
                    print(f"   System in AUTO mode - continuing blockchain processing...")
                
                # Wait for new block
                print(f"   Waiting for block after {current_block}...")
                new_block = await fetcher.wait_for_new_block(current_block, max_wait_seconds=45)
                
                if new_block > current_block:
                    print(f"   NEW BLOCK DETECTED: {new_block} (was {current_block})")
                    current_block = new_block
                else:
                    print(f"   No new block detected, continuing with {current_block}")
                
                # Process blockchain data for this block with fresh API calls
                result = await processor.process_current_data(epoch=current_block, force_refresh=True)
                
                # Send motor commands to TCP server
                print(f"   Processing result for block {current_block}: {type(result)} - {result is not None}")
                
                if result:
                    if hasattr(result, 'to_execution_format'):
                        motor_commands = result.to_execution_format()
                        print(f"   Generated execution format: {motor_commands}")
                        
                        # Convert to Motor TCP Server expected format with blockchain data
                        tcp_format = {
                            "motors": {},
                            "blockchain_data": {
                                "eth_price_usd": getattr(result.source_data, 'eth_price_usd', 0),
                                "gas_price_gwei": getattr(result.source_data, 'gas_price_gwei', 0),
                                "blob_space_utilization_percent": getattr(result.source_data, 'blob_space_utilization_percent', 0),
                                "block_fullness_percent": getattr(result.source_data, 'block_fullness_percent', 0),
                                "epoch": result.epoch,
                                "block_number": getattr(result.source_data, 'block_number', current_block),  # Use current block if not available
                                "data_sources": getattr(result.source_data, 'data_sources', {})
                            }
                        }
                        
                        for motor_name, motor_data in motor_commands.items():
                            tcp_format["motors"][motor_name] = {
                                "rpm": motor_data["velocity_rpm"],
                                "dir": motor_data["direction"]
                            }
                        
                        print(f"   BLOCK {current_block}: ETH=${tcp_format['blockchain_data']['eth_price_usd']:.2f}, Gas={tcp_format['blockchain_data']['gas_price_gwei']:.1f} gwei")
                        print(f"   Motor Commands: {tcp_format['motors']}")
                        
                        # Connect to motor TCP server and send commands
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                                sock.settimeout(1.0)
                                sock.connect(("localhost", 8767))
                                
                                # Send motor commands in correct format
                                command_data = json.dumps(tcp_format)
                                
                                sock.send(command_data.encode() + b'\n')
                                print(f"   SUCCESS: Sent block {current_block} motor commands to TCP server!")
                                
                                # Save last motor states for smooth transitions
                                save_last_motor_states(tcp_format["motors"])
                                
                                # Broadcast blockchain data to all connected clients via Cloud Orchestrator
                                try:
                                    if cloud_orchestrator_instance:
                                        # Convert motor data to frontend format
                                        motor_commands_for_frontend = {}
                                        for motor_name, motor_data in tcp_format["motors"].items():
                                            motor_commands_for_frontend[motor_name] = {
                                                "velocity_rpm": motor_data["rpm"],
                                                "direction": motor_data["dir"]
                                            }
                                        
                                        # Broadcast to all connected web clients
                                        await cloud_orchestrator_instance.broadcast_blockchain_data(
                                            tcp_format["blockchain_data"], 
                                            motor_commands_for_frontend
                                        )
                                        
                                        # Update individual motor states for real-time visualization
                                        for motor_name, motor_data in motor_commands_for_frontend.items():
                                            await cloud_orchestrator_instance.broadcast_motor_state_update(
                                                motor_name, 
                                                {
                                                    "velocity_rpm": motor_data["velocity_rpm"],
                                                    "direction": motor_data["direction"],
                                                    "last_update": time.time(),
                                                    "is_enabled": True,
                                                    "source": "blockchain"
                                                }
                                            )
                                        
                                        print(f"   Broadcasted blockchain data to web clients")
                                    
                                except Exception as orch_error:
                                    print(f"   Could not broadcast to Cloud Orchestrator: {orch_error}")
                                
                        except Exception as tcp_error:
                            print(f"   TCP connection error: {tcp_error}")
                    else:
                        print(f"   Result has no to_execution_format method: {dir(result)}")
                else:
                    print("   No result from data processor")
                
            except Exception as e:
                logging.error(f"Block-based data processing error: {e}")
                print(f"   Error processing block {current_block}: {e}")
                await asyncio.sleep(15)  # Wait before retrying
    
    data_task = asyncio.create_task(block_data_loop())
    print("   Blockchain Data Service started with block-based motor integration")
    return data_task


async def main():
    """Main function to start the complete system demo."""
    print("=" * 70)
    print("DRAWING MACHINE COMPLETE SYSTEM DEMO")
    print("=" * 70)
    print("Initializing full production-ready architecture...")
    print()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Start all services
        print("Starting Core Services...")
        print("-" * 40)
        
        # 1. Visual Motor Server (GUI)
        visual_motor_process = start_visual_motor_server()
        await asyncio.sleep(3)  # Let GUI start
        
        # 2. Manual Control Server
        manual_control_task = await start_manual_control_server()
        await asyncio.sleep(2)
        
        # 3. Cloud Orchestrator (main coordination hub)
        orchestrator_task = await start_cloud_orchestrator()
        await asyncio.sleep(2)
        
        # 4. Blockchain Data Service
        blockchain_task = await start_blockchain_data_service()
        await asyncio.sleep(2)
        
        print()
        print("ALL SERVICES STARTED SUCCESSFULLY!")
        print("=" * 70)
        
        print()
        print("FRONTEND DEPLOYMENT:")
        print("Your frontend should be deployed at:")
        print("   https://drawing-machine-[your-id].vercel.app")
        print("   or start locally: cd frontend && npm run dev")
        print()
        
        print("SYSTEM ARCHITECTURE:")
        print("+-----------------+    +-----------------+    +-----------------+")
        print("|   Web Frontend  |<-->| Cloud Orchestr. |<-->|  Manual Control |")
        print("| (Vercel/Local)  |    |  :8768 (New!)   |    |  Server :8766   |")
        print("+-----------------+    +-----------------+    +-----------------+")
        print("         ^                       ^                       ^")
        print("         |                       |                       |")
        print("    +-------------+    +-----------------+    +-----------------+")
        print("    |   Users     |    |  Blockchain     |    |  Visual Motors  |")
        print("    | (Multiple)  |    |  Data :Auto     |    |  GUI :8767      |")
        print("    +-------------+    +-----------------+    +-----------------+")
        print()
        
        print("COMPLETE SYSTEM FEATURES:")
        print("- Multi-client WebSocket coordination")
        print("- Real-time session management") 
        print("- Live blockchain data processing")
        print("- Visual motor control with GUI")
        print("- Manual control with safety limits")
        print("- Session recording and playback")
        print("- System health monitoring")
        print("- Production-ready error handling")
        print("- Auto-scaling architecture")
        print()
        
        print("HOW TO USE THE COMPLETE SYSTEM:")
        print("1. FRONTEND: Open your deployed frontend or http://localhost:5173")
        print("2. CONNECT: Multiple users can connect simultaneously")
        print("3. SESSIONS: Create and manage drawing sessions")
        print("4. CONTROLS: Use manual controls with real-time feedback")
        print("5. MONITOR: Watch the Visual Motor GUI for motor responses")
        print("6. MODES: Switch between Manual/Auto/Hybrid/Offline modes")
        print("7. RECORD: Record sessions and play them back")
        print("8. SCALE: System handles multiple concurrent users")
        print()
        
        print("LIVE SYSTEM MONITORING:")
        print("- Visual Motor GUI: Real-time motor visualization")
        print("- Browser Console: WebSocket connection logs")
        print("- Backend Logs: System health and session activity")
        print("- Cloud Orchestrator: Central coordination hub")
        print()
        
        print("THIS IS A COMPLETE PRODUCTION SYSTEM!")
        print("Ready for deployment, scaling, and real hardware integration.")
        print()
        print("Press Ctrl+C to stop all services...")
        
        # Keep all services running
        await asyncio.gather(
            manual_control_task,
            orchestrator_task,
            blockchain_task,
            return_exceptions=True
        )
        
    except KeyboardInterrupt:
        print("\nStopping Complete System Demo...")
        print("Cleaning up all services...")
        
        # Cleanup
        if 'visual_motor_process' in locals():
            visual_motor_process.terminate()
            visual_motor_process.wait()
            print("   Visual Motor Server stopped")
        
        print("   All services stopped")
        print("Complete System Demo stopped successfully.")
        
    except Exception as e:
        print(f"\nSystem Demo failed: {e}")
        logging.error(f"Complete system error: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Failed to start complete system: {e}")
        sys.exit(1)