"""
Hardware Interface for Drawing Machine Motor Controller

High-level interface that coordinates motor driver and safety controller
for complete motor control system management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .motor_driver import ConnectionStatus, MotorDriver, MotorDriverError, MotorStatus
from .safety_controller import SafetyAlert, SafetyController, SafetyLevel, SafetyViolationError
from shared.models.motor_commands import MotorName, MotorSafetyLimits, MotorVelocityCommands


class HardwareInterface:
    """
    High-level hardware interface for drawing machine motor control.
    
    Coordinates motor driver, safety controller, and provides unified
    API for motor operations with comprehensive safety monitoring.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8888,
        safety_limits: Optional[MotorSafetyLimits] = None,
    ):
        self.motor_driver = MotorDriver(host, port, safety_limits)
        self.safety_controller = SafetyController(
            safety_limits or self.motor_driver.safety_limits
        )
        
        # Status tracking
        self._last_command_time: Optional[datetime] = None
        self._command_count = 0
        self._error_count = 0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """
        Initialize hardware interface and establish motor controller connection.
        
        Returns:
            bool: True if initialization successful
            
        Raises:
            MotorDriverError: If connection fails
        """
        try:
            self.logger.info("Initializing hardware interface...")
            
            # Connect to motor controller
            await self.motor_driver.connect()
            self.logger.info(f"Connected to motor controller at {self.motor_driver.host}:{self.motor_driver.port}")
            
            # Start background monitoring tasks
            await self._start_background_tasks()
            
            self.logger.info("Hardware interface initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hardware interface: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown hardware interface and cleanup resources."""
        self.logger.info("Shutting down hardware interface...")
        
        try:
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Emergency stop all motors
            await self.emergency_stop()
            
            # Disconnect from motor controller
            await self.motor_driver.disconnect()
            
            self.logger.info("Hardware interface shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def execute_motor_commands(self, commands: MotorVelocityCommands) -> bool:
        """
        Execute motor velocity commands with safety validation.
        
        Args:
            commands: Motor velocity commands to execute
            
        Returns:
            bool: True if commands executed successfully
            
        Raises:
            SafetyViolationError: If commands violate safety limits
            MotorDriverError: If motor driver communication fails
        """
        try:
            self.logger.debug(f"Executing motor commands: {commands.session_id}")
            
            # Validate commands through safety controller
            await self.safety_controller.validate_motor_commands(commands)
            
            # Update motor timing for active motors
            await self._update_motor_timing(commands)
            
            # Send commands to motor driver
            success = await self.motor_driver.send_motor_commands(commands)
            
            if success:
                self._command_count += 1
                self._last_command_time = datetime.now()
                self.logger.debug(f"Motor commands executed successfully")
            
            return success
            
        except SafetyViolationError as e:
            self.logger.error(f"Safety violation: {e}")
            await self.emergency_stop()
            raise
            
        except MotorDriverError as e:
            self.logger.error(f"Motor driver error: {e}")
            self._error_count += 1
            raise
    
    async def emergency_stop(self) -> None:
        """Execute emergency stop procedure."""
        self.logger.warning("Emergency stop initiated")
        
        try:
            # Activate safety controller emergency stop
            await self.safety_controller.emergency_stop()
            
            # Send emergency stop to motor driver
            await self.motor_driver.emergency_stop()
            
            self.logger.warning("Emergency stop completed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
            raise
    
    async def reset_emergency_stop(self) -> None:
        """Reset emergency stop condition."""
        self.logger.info("Resetting emergency stop")
        
        try:
            # Reset safety controller first
            await self.safety_controller.reset_emergency_stop()
            
            self.logger.info("Emergency stop reset - normal operations can resume")
            
        except SafetyViolationError as e:
            self.logger.error(f"Cannot reset emergency stop: {e}")
            raise
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        motor_statuses = await self.motor_driver.get_all_motor_status()
        active_alerts = await self.safety_controller.get_active_alerts()
        
        return {
            "connection_status": self.motor_driver.connection_status.value,
            "safety_level": self.safety_controller.system_status.value,
            "emergency_stop_active": self.safety_controller.emergency_stop_active,
            "motor_statuses": {
                motor_name.value: {
                    "current_velocity": status.current_velocity,
                    "target_velocity": status.target_velocity,
                    "direction": status.direction.value,
                    "is_moving": status.is_moving,
                    "last_command_time": status.last_command_time.isoformat(),
                    "error_count": status.error_count,
                    "temperature": status.temperature,
                }
                for motor_name, status in motor_statuses.items()
            },
            "active_alerts": [
                {
                    "level": alert.level.value,
                    "message": alert.message,
                    "motor_name": alert.motor_name.value if alert.motor_name else None,
                    "timestamp": alert.timestamp.isoformat(),
                    "violation_type": alert.violation_type,
                }
                for alert in active_alerts
            ],
            "statistics": {
                "command_count": self._command_count,
                "error_count": self._error_count,
                "last_command_time": self._last_command_time.isoformat() if self._last_command_time else None,
            }
        }
    
    async def get_motor_status(self, motor_name: MotorName) -> MotorStatus:
        """Get status of a specific motor."""
        return await self.motor_driver.get_motor_status(motor_name)
    
    async def get_safety_alerts(self) -> List[SafetyAlert]:
        """Get all active safety alerts."""
        return await self.safety_controller.get_active_alerts()
    
    async def update_motor_temperature(self, motor_name: MotorName, temperature: float) -> None:
        """Update motor temperature reading."""
        await self.safety_controller.update_motor_temperature(motor_name, temperature)
    
    @property
    def is_connected(self) -> bool:
        """Check if hardware interface is connected."""
        return self.motor_driver.is_connected
    
    @property
    def connection_status(self) -> ConnectionStatus:
        """Get connection status."""
        return self.motor_driver.connection_status
    
    @property
    def safety_level(self) -> SafetyLevel:
        """Get current safety level."""
        return self.safety_controller.system_status
    
    async def _start_background_tasks(self) -> None:
        """Start background monitoring and heartbeat tasks."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _heartbeat_loop(self) -> None:
        """Background heartbeat task to maintain connection."""
        while True:
            try:
                if self.motor_driver.is_connected:
                    await self.motor_driver.heartbeat()
                await asyncio.sleep(10)  # Heartbeat every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring task for system health."""
        while True:
            try:
                # Check for temperature warnings
                # Check for connection health
                # Monitor safety alerts
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _update_motor_timing(self, commands: MotorVelocityCommands) -> None:
        """Update motor operation timing based on commands."""
        motor_velocities = [
            (MotorName.CANVAS, commands.canvas_velocity_rpm),
            (MotorName.PEN_BRUSH, commands.pen_brush_velocity_rpm),
            (MotorName.PEN_COLOR_DEPTH, commands.pen_color_depth_velocity_rpm),
            (MotorName.PEN_ELEVATION, commands.pen_elevation_velocity_rpm),
        ]
        
        for motor_name, velocity in motor_velocities:
            if velocity > 0:
                await self.safety_controller.start_motor_timing(motor_name)
            else:
                await self.safety_controller.stop_motor_timing(motor_name)