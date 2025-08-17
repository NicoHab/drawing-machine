import asyncio
import json
import logging
import time
from dataclasses import dataclass

@dataclass
class MotorState:
    rpm: float = 0.0
    direction: str = "CW"

class MockMotorControllerTCP:
    def __init__(self, port=8765):
        self.port = port
        self.motors = {
            "canvas": MotorState(),
            "pb": MotorState(),
            "pcd": MotorState(),
            "pe": MotorState()
        }
        self.command_count = 0
        
    async def handle_client(self, reader, writer):
        print("Client connected")
        while True:
            try:
                data = await reader.readline()
                if not data:
                    break
                    
                command = json.loads(data.decode().strip())
                self.command_count += 1
                
                # Update motors
                for name, cmd in command.get("motors", {}).items():
                    if name in self.motors:
                        self.motors[name].rpm = cmd.get("rpm", 0)
                        self.motors[name].direction = cmd.get("dir", "CW")
                
                print(f"Command {self.command_count}: Canvas={self.motors['canvas'].rpm}RPM")
                
                # Send response
                response = {
                    "status": "ACK",
                    "command_id": self.command_count,
                    "motors": {name: {"rpm": m.rpm, "direction": m.direction} 
                              for name, m in self.motors.items()}
                }
                
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()
                
            except Exception as e:
                print(f"Error: {e}")
                break
                
        writer.close()
        await writer.wait_closed()
    
    async def start(self):
        server = await asyncio.start_server(self.handle_client, 'localhost', self.port)
        print(f"Mock Motor Controller running on localhost:{self.port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    controller = MockMotorControllerTCP()
    asyncio.run(controller.start())