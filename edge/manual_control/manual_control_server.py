"""
Manual Control Server

WebSocket-based server for real-time manual control of drawing machine motors.
Provides direct user control with safety limits and session recording.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

import websockets
from websockets.server import WebSocketServerProtocol

from shared.models.motor_commands import (
    MotorName,
    MotorDirection, 
    SingleMotorCommand,
    MotorSafetyLimits,
    MotorCommandError
)


class ControlMode(str, Enum):
    """Control modes for the manual control system."""
    MANUAL = "manual"
    AUTO = "auto"
    HYBRID = "hybrid"
    OFFLINE = "offline"


@dataclass
class ManualCommand:
    """Manual motor command from user input."""
    motor_name: str
    velocity_rpm: float
    direction: str
    timestamp: float
    source: str = "manual"  # manual, joystick, keyboard


@dataclass
class SessionRecording:
    """Recording of a manual control session."""
    session_id: str
    start_time: float
    end_time: Optional[float]
    commands: List[ManualCommand]
    mode: ControlMode
    metadata: Dict


class ManualControlServer:
    """
    WebSocket server for real-time manual motor control.
    
    Features:
    - Real-time motor control via WebSocket
    - Safety limit enforcement
    - Session recording and playback
    - Multiple control modes
    - Multi-client support
    """
    
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Connected clients
        self.clients: Set[WebSocketServerProtocol] = set()
        
        # Current system state
        self.current_mode = ControlMode.MANUAL
        self.safety_limits = MotorSafetyLimits()
        self.is_emergency_stopped = False
        
        # Motor states
        self.motor_states = {
            motor.value: {
                "velocity_rpm": 0.0,
                "direction": MotorDirection.CLOCKWISE.value,
                "last_update": time.time(),
                "is_enabled": True
            }
            for motor in MotorName
        }
        
        # Session recording
        self.current_session: Optional[SessionRecording] = None
        self.recorded_sessions: List[SessionRecording] = []
        
        # TCP motor communication
        self.motor_tcp_host = "localhost"
        self.motor_tcp_port = 8767
        
    async def start_server(self):
        """Start the WebSocket server."""
        self.logger.info(f"Starting manual control server on {self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            self.logger.info("Manual control server started")
            # Keep server running
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle new WebSocket client connection."""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        self.logger.info(f"Client connected: {client_addr}")
        
        try:
            # Send initial state to new client
            await self.send_system_state(websocket)
            
            # Handle messages from client
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming WebSocket message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "motor_command":
                await self.handle_motor_command(data)
            elif message_type == "emergency_stop":
                await self.handle_emergency_stop()
            elif message_type == "mode_change":
                await self.handle_mode_change(data.get("mode"))
            elif message_type == "start_recording":
                await self.start_session_recording(data.get("session_name", ""))
            elif message_type == "stop_recording":
                await self.stop_session_recording()
            elif message_type == "playback_session":
                await self.playback_session(data.get("session_id"))
            elif message_type == "get_recordings":
                await self.send_recordings_list(websocket)
            elif message_type == "ping":
                await websocket.send(json.dumps({"type": "pong", "timestamp": time.time()}))
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON received: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error", 
                "message": str(e)
            }))
    
    async def handle_motor_command(self, data: Dict):
        """Handle motor command from client."""
        if self.is_emergency_stopped:
            self.logger.warning("Motor command rejected - emergency stop active")
            return
            
        try:
            motor_name = data.get("motor_name")
            velocity_rpm = float(data.get("velocity_rpm", 0))
            direction = data.get("direction", "CW")
            source = data.get("source", "manual")
            
            # Validate motor name
            if motor_name not in [motor.value for motor in MotorName]:
                raise MotorCommandError(f"Invalid motor name: {motor_name}")
            
            # Validate direction
            if direction not in [MotorDirection.CLOCKWISE.value, MotorDirection.COUNTER_CLOCKWISE.value]:
                raise MotorCommandError(f"Invalid direction: {direction}")
            
            # Apply safety limits
            motor_enum = MotorName(motor_name)
            max_rpm = self.safety_limits.get_limit_for_motor(motor_enum)
            velocity_rpm = max(-max_rpm, min(max_rpm, velocity_rpm))
            
            # Update motor state
            self.motor_states[motor_name] = {
                "velocity_rpm": velocity_rpm,
                "direction": direction,
                "last_update": time.time(),
                "is_enabled": True
            }
            
            # Record command if session is active
            if self.current_session:
                command = ManualCommand(
                    motor_name=motor_name,
                    velocity_rpm=velocity_rpm,
                    direction=direction,
                    timestamp=time.time(),
                    source=source
                )
                self.current_session.commands.append(command)
            
            # Send command to motor TCP server
            await self.send_to_motor_tcp({
                "motor_name": motor_name,
                "velocity_rpm": velocity_rpm,
                "direction": direction,
                "timestamp": time.time()
            })
            
            # Broadcast updated state to all clients
            await self.broadcast_motor_update(motor_name)
            
            self.logger.info(f"Motor command: {motor_name} -> {velocity_rpm} RPM {direction}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle motor command: {e}")
            await self.broadcast_error(f"Motor command failed: {str(e)}")
    
    async def handle_emergency_stop(self):
        """Handle emergency stop command."""
        self.logger.warning("EMERGENCY STOP ACTIVATED")
        self.is_emergency_stopped = True
        
        # Stop all motors
        for motor_name in self.motor_states:
            self.motor_states[motor_name] = {
                "velocity_rpm": 0.0,
                "direction": MotorDirection.CLOCKWISE.value,
                "last_update": time.time(),
                "is_enabled": False
            }
        
        # Send stop commands to motor TCP server
        for motor_name in MotorName:
            await self.send_to_motor_tcp({
                "motor_name": motor_name.value,
                "velocity_rpm": 0.0,
                "direction": MotorDirection.CLOCKWISE.value,
                "timestamp": time.time(),
                "emergency_stop": True
            })
        
        # Broadcast emergency stop to all clients
        await self.broadcast_message({
            "type": "emergency_stop",
            "timestamp": time.time(),
            "message": "Emergency stop activated - all motors stopped"
        })
    
    async def handle_mode_change(self, new_mode: str):
        """Handle control mode change."""
        try:
            mode = ControlMode(new_mode)
            old_mode = self.current_mode
            self.current_mode = mode
            
            self.logger.info(f"Mode changed: {old_mode.value} -> {mode.value}")
            
            # Reset emergency stop when switching to manual mode
            if mode == ControlMode.MANUAL:
                self.is_emergency_stopped = False
            
            await self.broadcast_message({
                "type": "mode_changed",
                "old_mode": old_mode.value,
                "new_mode": mode.value,
                "timestamp": time.time()
            })
            
        except ValueError:
            self.logger.error(f"Invalid control mode: {new_mode}")
            await self.broadcast_error(f"Invalid control mode: {new_mode}")
    
    async def start_session_recording(self, session_name: str):
        """Start recording a manual control session."""
        if self.current_session:
            await self.stop_session_recording()
        
        session_id = f"session_{int(time.time())}"
        self.current_session = SessionRecording(
            session_id=session_id,
            start_time=time.time(),
            end_time=None,
            commands=[],
            mode=self.current_mode,
            metadata={
                "name": session_name or f"Session {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "safety_limits": asdict(self.safety_limits)
            }
        )
        
        self.logger.info(f"Started recording session: {session_id}")
        await self.broadcast_message({
            "type": "recording_started",
            "session_id": session_id,
            "session_name": self.current_session.metadata["name"],
            "timestamp": time.time()
        })
    
    async def stop_session_recording(self):
        """Stop recording the current session."""
        if not self.current_session:
            return
        
        self.current_session.end_time = time.time()
        self.recorded_sessions.append(self.current_session)
        
        duration = self.current_session.end_time - self.current_session.start_time
        command_count = len(self.current_session.commands)
        
        self.logger.info(f"Stopped recording session: {self.current_session.session_id} "
                        f"({duration:.1f}s, {command_count} commands)")
        
        await self.broadcast_message({
            "type": "recording_stopped",
            "session_id": self.current_session.session_id,
            "duration": duration,
            "command_count": command_count,
            "timestamp": time.time()
        })
        
        self.current_session = None
    
    async def playback_session(self, session_id: str):
        """Playback a recorded session."""
        # Find session
        session = None
        for recorded_session in self.recorded_sessions:
            if recorded_session.session_id == session_id:
                session = recorded_session
                break
        
        if not session:
            await self.broadcast_error(f"Session not found: {session_id}")
            return
        
        self.logger.info(f"Starting playback of session: {session_id}")
        await self.broadcast_message({
            "type": "playback_started",
            "session_id": session_id,
            "command_count": len(session.commands),
            "timestamp": time.time()
        })
        
        # Playback commands with original timing
        start_time = session.commands[0].timestamp if session.commands else time.time()
        
        for command in session.commands:
            # Calculate delay based on original timing
            relative_time = command.timestamp - start_time
            current_relative = time.time() - time.time()  # Reset base
            
            if relative_time > current_relative:
                await asyncio.sleep(relative_time - current_relative)
            
            # Execute command
            await self.handle_motor_command({
                "motor_name": command.motor_name,
                "velocity_rpm": command.velocity_rpm,
                "direction": command.direction,
                "source": "playback"
            })
        
        await self.broadcast_message({
            "type": "playback_completed",
            "session_id": session_id,
            "timestamp": time.time()
        })
    
    async def send_recordings_list(self, websocket: WebSocketServerProtocol):
        """Send list of recorded sessions to client."""
        recordings = []
        for session in self.recorded_sessions:
            recordings.append({
                "session_id": session.session_id,
                "name": session.metadata.get("name", "Unnamed Session"),
                "start_time": session.start_time,
                "duration": (session.end_time or time.time()) - session.start_time,
                "command_count": len(session.commands),
                "mode": session.mode.value
            })
        
        await websocket.send(json.dumps({
            "type": "recordings_list",
            "recordings": recordings,
            "timestamp": time.time()
        }))
    
    async def send_to_motor_tcp(self, command: Dict):
        """Send command to motor TCP server."""
        try:
            reader, writer = await asyncio.open_connection(
                self.motor_tcp_host, self.motor_tcp_port
            )
            
            command_json = json.dumps(command) + "\n"
            writer.write(command_json.encode())
            await writer.drain()
            
            # Read response
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            
            self.logger.debug(f"Motor TCP response: {response.decode().strip()}")
            
        except Exception as e:
            self.logger.warning(f"Failed to send to motor TCP: {e}")
    
    async def send_system_state(self, websocket: WebSocketServerProtocol):
        """Send current system state to client."""
        state = {
            "type": "system_state",
            "mode": self.current_mode.value,
            "emergency_stopped": self.is_emergency_stopped,
            "motor_states": self.motor_states,
            "safety_limits": {
                "canvas_max": self.safety_limits.motor_canvas_max_rpm,
                "pb_max": self.safety_limits.motor_pb_max_rpm,
                "pcd_max": self.safety_limits.motor_pcd_max_rpm,
                "pe_max": self.safety_limits.motor_pe_max_rpm
            },
            "recording_active": self.current_session is not None,
            "timestamp": time.time()
        }
        
        await websocket.send(json.dumps(state))
    
    async def broadcast_motor_update(self, motor_name: str):
        """Broadcast motor state update to all clients."""
        message = {
            "type": "motor_update",
            "motor_name": motor_name,
            "state": self.motor_states[motor_name],
            "timestamp": time.time()
        }
        await self.broadcast_message(message)
    
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    async def broadcast_error(self, error_message: str):
        """Broadcast error message to all clients."""
        await self.broadcast_message({
            "type": "error",
            "message": error_message,
            "timestamp": time.time()
        })


async def main():
    """Main function to start the manual control server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = ManualControlServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logging.info("Manual control server stopped")


if __name__ == "__main__":
    asyncio.run(main())