#!/usr/bin/env python3
"""
Manual Control Demo

Demonstrates the manual control system with both backend WebSocket server
and frontend web interface working together.
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path


async def start_mock_motor_server():
    """Start the mock motor TCP server."""
    print("Starting mock motor TCP server...")
    
    # Run the mock motor server
    process = await asyncio.create_subprocess_exec(
        sys.executable, "tools/mock_motor_tcp.py",
        cwd=Path(__file__).parent,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    print(f"   Mock motor server started (PID: {process.pid})")
    return process


async def start_manual_control_server():
    """Start the manual control WebSocket server."""
    print("Starting manual control WebSocket server...")
    
    from edge.manual_control.manual_control_server import ManualControlServer
    
    server = ManualControlServer(host="localhost", port=8766)
    
    # Start server in background
    server_task = asyncio.create_task(server.start_server())
    print("   Manual control server started on ws://localhost:8766")
    
    return server_task


def start_frontend_dev_server():
    """Start the Vue.js frontend development server."""
    print("Starting frontend development server...")
    
    frontend_path = Path(__file__).parent / "frontend"
    
    # Start npm dev server
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"   Frontend dev server started (PID: {process.pid})")
    print("   Frontend will be available at: http://localhost:5173")
    
    return process


async def main():
    """Main demo function."""
    print("Drawing Machine Manual Control Demo")
    print("=" * 50)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Start components
        mock_motor_process = await start_mock_motor_server()
        await asyncio.sleep(2)  # Let mock server start
        
        manual_control_task = await start_manual_control_server()
        await asyncio.sleep(2)  # Let WebSocket server start
        
        frontend_process = start_frontend_dev_server()
        await asyncio.sleep(5)  # Let frontend start
        
        print("\nAll services started successfully!")
        print("\nDemo Instructions:")
        print("1. Open your browser to: http://localhost:5173")
        print("2. Navigate to: Manual Control")
        print("3. Click 'Connect' to connect to WebSocket server")
        print("4. Try controlling the motors with sliders and presets")
        print("5. Test emergency stop functionality")
        print("6. Record a session and play it back")
        print("7. Switch between different control modes")
        
        print("\nWhat to observe:")
        print("- Real-time motor control via web interface")
        print("- Motor states updating in real-time")
        print("- Safety limits being enforced")
        print("- Session recording and playback")
        print("- TCP communication with mock motor server")
        
        print("\nPress Ctrl+C to stop all services")
        
        # Keep running until interrupted
        await manual_control_task
        
    except KeyboardInterrupt:
        print("\nStopping demo...")
        
        # Clean up processes
        if 'mock_motor_process' in locals():
            mock_motor_process.terminate()
            await mock_motor_process.wait()
        
        if 'frontend_process' in locals():
            frontend_process.terminate()
            frontend_process.wait()
        
        print("Demo stopped.")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        logging.error(f"Demo error: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Failed to start demo: {e}")
        sys.exit(1)