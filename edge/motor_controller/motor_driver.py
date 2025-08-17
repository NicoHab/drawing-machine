"""
Motor Driver Implementation for Drawing Machine

Provides low-level motor control interface with safety checks and real-time feedback.
"""

import asyncio
import json
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from shared.models.motor_commands import (
    MotorCommandError,
    MotorDirection,
    MotorName,
    MotorSafetyLimits,
    MotorVelocityCommands,
)


class MotorDriverError(Exception):
    """Exception raised for motor driver related errors."""
    
    def __init__(self, message: str, motor_name: Optional[str] = None):
        self.motor_name = motor_name
        super().__init__(message)


class ConnectionStatus(str, Enum):
    """Motor driver connection status."""
    
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MotorStatus:
    """Current status of a motor."""
    
    name: MotorName
    current_velocity: float
    target_velocity: float
    direction: MotorDirection
    is_moving: bool
    last_command_time: datetime
    error_count: int = 0
    temperature: Optional[float] = None


class MotorDriver:
    """
    Low-level motor driver for the drawing machine.
    
    Handles TCP communication with motor controllers and provides
    real-time control and feedback capabilities.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8888,
        safety_limits: Optional[MotorSafetyLimits] = None,
    ):
        self.host = host
        self.port = port
        self.safety_limits = safety_limits or self._default_safety_limits()
        
        self._socket: Optional[socket.socket] = None
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._motor_statuses: Dict[MotorName, MotorStatus] = {}
        self._last_heartbeat = datetime.now()
        
        # Initialize motor statuses
        for motor_name in MotorName:
            self._motor_statuses[motor_name] = MotorStatus(
                name=motor_name,
                current_velocity=0.0,
                target_velocity=0.0,
                direction=MotorDirection.CLOCKWISE,
                is_moving=False,
                last_command_time=datetime.now(),
            )
    
    def _default_safety_limits(self) -> MotorSafetyLimits:
        """Create default safety limits for motors."""
        return MotorSafetyLimits(
            motor_canvas_max_rpm=35.0,
            motor_pb_max_rpm=25.0,
            motor_pcd_max_rpm=20.0,
            motor_pe_max_rpm=30.0,
            emergency_stop_rpm=0.0,
        )
    
    async def connect(self) -> bool:
        """
        Establish connection to motor controller hardware.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._connection_status = ConnectionStatus.CONNECTING
            
            # Create TCP socket connection
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)  # 5 second timeout
            
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.connect, (self.host, self.port)
            )
            
            self._connection_status = ConnectionStatus.CONNECTED
            self._last_heartbeat = datetime.now()
            
            # Send initialization command
            await self._send_command({"type": "init", "timestamp": time.time()})
            
            return True
            
        except (socket.error, OSError) as e:
            self._connection_status = ConnectionStatus.ERROR
            raise MotorDriverError(f"Failed to connect to motor controller: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from motor controller."""
        if self._socket:
            try:
                # Send stop command before disconnecting
                await self.emergency_stop()
                await self._send_command({"type": "disconnect"})
            except Exception:
                pass  # Ignore errors during shutdown
            finally:
                self._socket.close()
                self._socket = None
                self._connection_status = ConnectionStatus.DISCONNECTED
    
    async def send_motor_commands(self, commands: MotorVelocityCommands) -> bool:
        """
        Send velocity commands to all motors.
        
        Args:
            commands: Motor velocity commands to execute
            
        Returns:
            bool: True if commands sent successfully
            
        Raises:
            MotorDriverError: If command fails or violates safety limits
        """
        if self._connection_status != ConnectionStatus.CONNECTED:
            raise MotorDriverError("Motor driver not connected")
        
        # Validate commands against safety limits
        self._validate_commands(commands)
        
        # Prepare command packet
        command_packet = {
            "type": "motor_commands",
            "timestamp": commands.timestamp,
            "epoch": commands.epoch,
            "motors": {}
        }
        
        # Convert motor commands to packet format
        for motor_name, motor_command in commands.motors.items():
            command_packet["motors"][motor_name] = {
                "velocity": motor_command.velocity_rpm,
                "direction": motor_command.direction.value,
            }
        
        # Send command
        await self._send_command(command_packet)
        
        # Update motor statuses
        self._update_motor_statuses(commands)
        
        return True
    
    async def emergency_stop(self) -> None:
        """Immediately stop all motors."""
        stop_command = {
            "type": "emergency_stop",
            "timestamp": time.time(),
        }
        
        await self._send_command(stop_command)
        
        # Update all motor statuses to stopped
        for motor_status in self._motor_statuses.values():
            motor_status.current_velocity = 0.0
            motor_status.target_velocity = 0.0
            motor_status.is_moving = False
            motor_status.last_command_time = datetime.now()
    
    async def get_motor_status(self, motor_name: MotorName) -> MotorStatus:
        """Get current status of a specific motor."""
        return self._motor_statuses[motor_name]
    
    async def get_all_motor_status(self) -> Dict[MotorName, MotorStatus]:
        """Get status of all motors."""
        return self._motor_statuses.copy()
    
    async def heartbeat(self) -> bool:
        """Send heartbeat to maintain connection."""
        try:
            heartbeat_command = {
                "type": "heartbeat",
                "timestamp": time.time(),
            }
            
            await self._send_command(heartbeat_command)
            self._last_heartbeat = datetime.now()
            return True
            
        except Exception as e:
            raise MotorDriverError(f"Heartbeat failed: {e}")
    
    @property
    def connection_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._connection_status
    
    @property
    def is_connected(self) -> bool:
        """Check if driver is connected."""
        return self._connection_status == ConnectionStatus.CONNECTED
    
    async def _send_command(self, command: Dict[str, Any]) -> None:
        """Send command to motor controller via TCP."""
        if not self._socket:
            raise MotorDriverError("No socket connection")
        
        try:
            command_json = json.dumps(command) + "\n"
            command_bytes = command_json.encode('utf-8')
            
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.sendall, command_bytes
            )
            
        except (socket.error, OSError) as e:
            self._connection_status = ConnectionStatus.ERROR
            raise MotorDriverError(f"Failed to send command: {e}")
    
    def _validate_commands(self, commands: MotorVelocityCommands) -> None:
        """Validate motor commands against safety limits."""
        for motor_name_str, motor_command in commands.motors.items():
            try:
                motor_name = MotorName(motor_name_str)
                velocity = motor_command.velocity_rpm
                
                if not self.safety_limits.validate_rpm(motor_name, abs(velocity)):
                    max_limit = self.safety_limits.get_limit_for_motor(motor_name)
                    raise MotorDriverError(
                        f"Motor {motor_name.value} velocity {abs(velocity)} exceeds max limit {max_limit}"
                    )
            except ValueError:
                raise MotorDriverError(f"Invalid motor name: {motor_name_str}")
    
    def _update_motor_statuses(self, commands: MotorVelocityCommands) -> None:
        """Update internal motor status tracking."""
        now = datetime.now()
        
        for motor_name_str, motor_command in commands.motors.items():
            try:
                motor_name = MotorName(motor_name_str)
                status = self._motor_statuses[motor_name]
                status.target_velocity = motor_command.velocity_rpm
                status.direction = motor_command.direction
                status.is_moving = abs(motor_command.velocity_rpm) > 0.0
                status.last_command_time = now
            except ValueError:
                continue  # Skip invalid motor names