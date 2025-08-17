import asyncio
import json
import time


async def test_tcp_communication():
    try:
        print("Connecting to mock motor controller...")
        reader, writer = await asyncio.open_connection("localhost", 8765)

        print("✅ Connected successfully!")

        # Test command
        command = {
            "timestamp": time.time(),
            "epoch": 1,
            "motors": {
                "canvas": {"rpm": 15.0, "dir": "CW"},
                "pb": {"rpm": 8.0, "dir": "CCW"},
            },
        }

        print(f"Sending command: {command}")

        # Send command
        command_str = json.dumps(command) + "\n"
        writer.write(command_str.encode())
        await writer.drain()

        # Read response
        response_data = await reader.readline()
        response = json.loads(response_data.decode().strip())

        print(f"Response: {response}")

        if response.get("status") == "ACK":
            print("✅ TCP communication test PASSED!")
            return True
        else:
            print("❌ Unexpected response")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(test_tcp_communication())
