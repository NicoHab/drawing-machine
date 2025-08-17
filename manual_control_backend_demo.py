#!/usr/bin/env python3
"""
Manual Control Backend Demo

Starts the WebSocket server and mock motor TCP server for manual control.
Frontend must be started separately with 'npm run dev' in the frontend directory.
"""

import asyncio
import logging
import sys
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


async def main():
    """Main demo function."""
    print("Drawing Machine Manual Control Backend Demo")
    print("=" * 60)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Start backend components
        mock_motor_process = await start_mock_motor_server()
        await asyncio.sleep(2)  # Let mock server start
        
        manual_control_task = await start_manual_control_server()
        await asyncio.sleep(2)  # Let WebSocket server start
        
        print("\nAll backend services started successfully!")
        print("\nTo start the frontend:")
        print("1. Open a new terminal/command prompt")
        print("2. Navigate to the frontend directory:")
        print("   cd frontend")
        print("3. Install dependencies (if not done already):")
        print("   npm install")
        print("4. Start the development server:")
        print("   npm run dev")
        print("5. Open your browser to: http://localhost:5173")
        print("6. Navigate to: Manual Control")
        print("7. Click 'Connect' to connect to WebSocket server")
        
        print("\nDemo Instructions:")
        print("- Use sliders to control motor velocity")
        print("- Click preset buttons for quick velocities")
        print("- Test emergency stop functionality")
        print("- Try recording and playing back sessions")
        print("- Switch between control modes")
        
        print("\nWhat to observe:")
        print("- Real-time motor control via web interface")
        print("- Motor states updating in real-time")
        print("- Safety limits being enforced")
        print("- Session recording and playback")
        print("- TCP communication with mock motor server")
        
        print("\nPress Ctrl+C to stop backend services")
        
        # Keep running until interrupted
        await manual_control_task
        
    except KeyboardInterrupt:
        print("\nStopping demo...")
        
        # Clean up processes
        if 'mock_motor_process' in locals():
            mock_motor_process.terminate()
            await mock_motor_process.wait()
        
        print("Backend demo stopped.")
        
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