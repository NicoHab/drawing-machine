#!/usr/bin/env python3
"""
Test Motor Command Format

Test the correct format for motor commands that the TCP server expects.
"""

import socket
import json
import time

def test_live_blockchain_format():
    """Test sending live blockchain data in correct format."""
    print("Testing Live Blockchain Motor Commands...")
    
    # Simulate real blockchain motor commands (like what the system generates)
    blockchain_commands = {
        "motor_canvas": {"velocity_rpm": 37.5, "direction": "CW", "duration_seconds": 3.4},
        "motor_pb": {"velocity_rpm": 15.4, "direction": "CCW", "duration_seconds": 3.4},
        "motor_pcd": {"velocity_rpm": 9.1, "direction": "CW", "duration_seconds": 3.4},
        "motor_pe": {"velocity_rpm": 13.5, "direction": "CCW", "duration_seconds": 3.4},
    }
    
    # Convert to Motor TCP Server expected format
    tcp_format = {
        "motors": {}
    }
    
    for motor_name, motor_data in blockchain_commands.items():
        tcp_format["motors"][motor_name] = {
            "rpm": motor_data["velocity_rpm"],
            "dir": motor_data["direction"]
        }
    
    print(f"Original format: {blockchain_commands}")
    print(f"TCP format: {tcp_format}")
    
    try:
        print("Connecting to Motor TCP Server...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect(("localhost", 8767))
            print("OK Connected successfully!")
            
            # Send motor commands in correct format
            command_data = json.dumps(tcp_format)
            
            print(f"Sending: {command_data}")
            sock.send(command_data.encode() + b'\n')
            print("OK Command sent successfully!")
            
            # Try to receive response
            try:
                response = sock.recv(1024)
                if response:
                    response_data = json.loads(response.decode())
                    print(f"OK Server response: {response_data}")
                else:
                    print("- No response received")
            except Exception as e:
                print(f"Response error: {e}")
                
        print("\nOK Live blockchain format test SUCCESSFUL!")
        print("Check the Visual Motor GUI - motors should be rotating!")
        print("Recent Commands should show: Multi-motor: motor_canvas: 37.5, motor_pb: 15.4, ...")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_live_blockchain_format()
    if success:
        print("\nThe motors should now be rotating with blockchain-like commands!")
        print("Watch the Visual Motor GUI for 10+ seconds to see the movement.")
    else:
        print("\nFailed to send commands. Make sure the complete system demo is running.")