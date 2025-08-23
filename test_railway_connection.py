#!/usr/bin/env python3
"""
Test Railway Deployment Connection
Test WebSocket connection to live Railway backend
"""

import asyncio
import websockets
import json

async def test_railway_connection():
    """Test connection to Railway deployed backend."""
    
    # Your Railway URL
    railway_url = "wss://drawing-machine-production.up.railway.app"
    
    print(f"Testing connection to Railway backend: {railway_url}")
    
    try:
        async with websockets.connect(railway_url) as websocket:
            print("✅ Connected to Railway backend successfully!")
            
            # Send a test message
            test_message = {
                "type": "connection_test",
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test message sent")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            print(f"📥 Received: {response_data}")
            
            print("🎉 Railway deployment test SUCCESSFUL!")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Check:")
        print("1. Railway deployment is running")
        print("2. URL is correct (wss:// not ws://)")
        print("3. Environment variables are set")

if __name__ == "__main__":
    asyncio.run(test_railway_connection())