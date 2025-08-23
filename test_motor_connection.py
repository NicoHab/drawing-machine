#!/usr/bin/env python3
"""
Test Motor TCP Connection

Simple test to check if we can connect to the motor TCP server
and send commands to make the GUI rotate.
"""

import socket
import json
import time

def test_motor_connection():
    """Test connection to motor TCP server."""
    print("Testing Motor TCP Server Connection...")
    
    # Test motor commands
    test_commands = {
        "motor_canvas": {"velocity_rpm": 50.0, "direction": "CW", "duration_seconds": 3.4},
        "motor_pb": {"velocity_rpm": 25.0, "direction": "CCW", "duration_seconds": 3.4},
        "motor_pcd": {"velocity_rpm": 15.0, "direction": "CW", "duration_seconds": 3.4},
        "motor_pe": {"velocity_rpm": 30.0, "direction": "CCW", "duration_seconds": 3.4},
    }
    
    try:
        print("Attempting to connect to localhost:8767...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect(("localhost", 8767))
            print("OK Connected successfully!")
            
            # Send test motor commands
            command_data = json.dumps({
                "type": "motor_commands",
                "commands": test_commands,
                "timestamp": time.time()
            })
            
            print(f"Sending command: {command_data[:100]}...")
            sock.send(command_data.encode() + b'\n')
            print("OK Command sent successfully!")
            
            # Try to receive response
            try:
                response = sock.recv(1024)
                if response:
                    print(f"OK Received response: {response.decode()[:100]}")
                else:
                    print("- No response received (this is normal for some TCP servers)")
            except:
                print("- No response received (this is normal for some TCP servers)")
                
        print("\nOK Motor TCP connection test SUCCESSFUL!")
        print("The Visual Motor GUI should now be rotating!")
        return True
        
    except ConnectionRefusedError:
        print("ERROR Connection refused - Motor TCP server not running on port 8767")
        return False
    except socket.timeout:
        print("ERROR Connection timeout - Motor TCP server not responding")
        return False
    except Exception as e:
        print(f"ERROR Connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_motor_connection()
    if success:
        print("\nIf the motor GUI is still not rotating, check:")
        print("1. Is the motor GUI window open?")
        print("2. Check the 'Recent Commands' section in the GUI")
        print("3. Look for any error messages in the GUI window")
    else:
        print("\nTroubleshooting:")
        print("1. Make sure the complete system demo is running")
        print("2. Check if port 8767 is being used by another process")
        print("3. Try restarting the complete system demo")