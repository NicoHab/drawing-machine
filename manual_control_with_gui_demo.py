#!/usr/bin/env python3
"""
Manual Control Demo with GUI Motor Visualization

Starts the WebSocket server and GUI motor TCP server for visual manual control.
Frontend must be started separately with 'npm run dev' in the frontend directory.
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path


def start_gui_motor_server():
    """Start the GUI mock motor TCP server."""
    print("Starting GUI mock motor TCP server...")
    
    # Start the GUI motor server
    process = subprocess.Popen(
        [sys.executable, "tools/mock_motor_tcp_gui.py"],
        cwd=Path(__file__).parent
    )
    
    print(f"   GUI motor server started (PID: {process.pid})")
    print("   Motor visualization window should appear")
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


async def main():
    """Main demo function."""
    print("Drawing Machine Manual Control with GUI Visualization")
    print("=" * 60)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Start GUI motor server first
        gui_motor_process = start_gui_motor_server()
        await asyncio.sleep(3)  # Give GUI server time to start
        
        # Start WebSocket server
        manual_control_task = await start_manual_control_server()
        await asyncio.sleep(2)  # Let WebSocket server start
        
        print("\nAll services started successfully!")
        print("\nTo start the frontend:")
        print("1. Open a new terminal/command prompt")
        print("2. Navigate to the frontend directory:")
        print("   cd frontend")
        print("3. Start the development server:")
        print("   npm run dev")
        print("4. Open your browser to: http://localhost:5173")
        print("5. Navigate to: Manual Control")
        print("6. Click 'Connect' to connect to WebSocket server")
        
        print("\nDemo Instructions:")
        print("- Use sliders to control motor velocity")
        print("- WATCH THE GUI WINDOW for visual motor feedback!")
        print("- Motor pointers rotate based on your controls")
        print("- Colors change with activity levels")
        print("- Command log shows real-time communication")
        print("- Try presets, directions, and emergency stop")
        
        print("\nWhat to observe:")
        print("- Real-time motor visualization with rotating pointers")
        print("- Color-coded activity levels (gray/green/orange/red)")
        print("- Live command log scrolling")
        print("- Server statistics updating")
        print("- Instant response to web controls")
        
        print("\nPress Ctrl+C to stop all services")
        
        # Keep running until interrupted
        await manual_control_task
        
    except KeyboardInterrupt:
        print("\nStopping demo...")
        
        # Clean up processes
        if 'gui_motor_process' in locals():
            gui_motor_process.terminate()
            gui_motor_process.wait()
        
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