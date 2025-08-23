#!/usr/bin/env python3
"""
Test Live Blockchain Visualization
Send real blockchain data to Motor TCP Server for visual verification
"""

import asyncio
import json
import socket
import time
from datetime import datetime

async def test_motor_visualization():
    """Send test blockchain data to motor server for visual verification."""
    
    print("Testing Live Blockchain Motor Visualization")
    print("=" * 60)
    
    # Connect to Motor TCP Server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8767))
        print("Connected to Motor TCP Server (localhost:8767)")
    except ConnectionRefusedError:
        print("ERROR: Motor TCP Server not running on localhost:8767")
        print("   Please make sure the motor GUI is running first!")
        return
    
    # Simulate live blockchain data updates
    test_data = [
        {
            "eth_price_usd": 3847.25,
            "gas_price_gwei": 28.5,
            "blob_space_utilization_percent": 72.3,
            "block_fullness_percent": 89.1,
            "epoch": 328475
        },
        {
            "eth_price_usd": 3851.80,
            "gas_price_gwei": 31.2,
            "blob_space_utilization_percent": 68.9,
            "block_fullness_percent": 85.7,
            "epoch": 328476
        },
        {
            "eth_price_usd": 3845.10,
            "gas_price_gwei": 35.8,
            "blob_space_utilization_percent": 81.2,
            "block_fullness_percent": 92.4,
            "epoch": 328477
        },
        {
            "eth_price_usd": 3858.95,
            "gas_price_gwei": 29.7,
            "blob_space_utilization_percent": 65.4,
            "block_fullness_percent": 78.3,
            "epoch": 328478
        }
    ]
    
    print("Sending live blockchain data to motors...")
    print("   Watch the Motor GUI for:")
    print("   - Clean logging format (1 line per motor)")
    print("   - Motor rotations based on blockchain data")
    print("   - Real ETH prices, gas prices, and epochs")
    print()
    
    for i, blockchain_data in enumerate(test_data):
        # Convert blockchain data to motor commands (simplified)
        eth_price = blockchain_data["eth_price_usd"]
        gas_price = blockchain_data["gas_price_gwei"]
        blob_util = blockchain_data["blob_space_utilization_percent"]
        block_full = blockchain_data["block_fullness_percent"]
        
        # Generate motor commands based on blockchain data
        motor_command = {
            "motors": {
                "motor_canvas": {
                    "rpm": min(eth_price / 50.0, 100.0),  # ETH price -> Canvas motor
                    "dir": "CW"
                },
                "motor_pb": {
                    "rpm": min(gas_price * 2.0, 100.0),  # Gas price -> Pen Brush
                    "dir": "CCW" if gas_price > 30 else "CW"
                },
                "motor_pcd": {
                    "rpm": min(blob_util * 0.8, 100.0),  # Blob utilization -> Pen Color Depth
                    "dir": "CW"
                },
                "motor_pe": {
                    "rpm": min(block_full * 0.6, 100.0),  # Block fullness -> Pen Elevation
                    "dir": "CCW" if block_full > 85 else "CW"
                }
            },
            "blockchain_data": blockchain_data
        }
        
        # Send to Motor TCP Server
        command_json = json.dumps(motor_command) + '\n'
        sock.send(command_json.encode())
        
        print(f"Epoch {blockchain_data['epoch']}: ETH=${eth_price:.2f}, Gas={gas_price:.1f}g")
        print(f"   -> Canvas: {motor_command['motors']['motor_canvas']['rpm']:.1f} RPM")
        print(f"   -> Pen Brush: {motor_command['motors']['motor_pb']['rpm']:.1f} RPM")
        print()
        
        # Wait 3 seconds between updates
        await asyncio.sleep(3)
    
    sock.close()
    print("Live blockchain visualization test complete!")
    print("   Check the Motor GUI for the clean log outputs and motor rotations")

if __name__ == "__main__":
    asyncio.run(test_motor_visualization())