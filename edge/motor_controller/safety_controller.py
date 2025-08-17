"""
Safety Controller for Drawing Machine Motors

Implements safety checks, emergency stop procedures, and motor protection systems.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

from shared.models.motor_commands import MotorName, MotorSafetyLimits, MotorVelocityCommands


class SafetyViolationError(Exception):
    """Exception raised when safety limits are violated."""
    
    def __init__(self, message: str, violation_type: str, motor_name: Optional[MotorName] = None):
        self.violation_type = violation_type
        self.motor_name = motor_name
        super().__init__(message)


class SafetyLevel(str, Enum):
    """Safety alert levels."""
    
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SafetyAlert:
    """Safety alert information."""
    
    level: SafetyLevel
    message: str
    motor_name: Optional[MotorName]
    timestamp: datetime
    violation_type: str
    resolved: bool = False


class SafetyController:
    """
    Safety controller for motor operations.
    
    Monitors motor commands and system state to prevent dangerous conditions
    and protect hardware from damage.
    """
    
    def __init__(self, safety_limits: MotorSafetyLimits):
        self.safety_limits = safety_limits
        self._active_alerts: List[SafetyAlert] = []
        self._emergency_stop_active = False
        self._motor_temperatures: Dict[MotorName, float] = {}
        self._motor_operation_time: Dict[MotorName, timedelta] = {
            motor: timedelta() for motor in MotorName
        }
        self._motor_last_start: Dict[MotorName, Optional[datetime]] = {
            motor: None for motor in MotorName
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def validate_motor_commands(self, commands: MotorVelocityCommands) -> bool:
        """
        Validate motor commands against safety limits.
        
        Args:
            commands: Motor velocity commands to validate
            
        Returns:
            bool: True if commands are safe, False otherwise
            
        Raises:
            SafetyViolationError: If commands violate critical safety limits
        """
        if self._emergency_stop_active:
            raise SafetyViolationError(
                "Emergency stop is active - no motor commands allowed",
                "emergency_stop_active"
            )
        
        # Check individual motor velocities
        for motor_name_str, motor_command in commands.motors.items():
            try:
                motor_name = MotorName(motor_name_str)
                velocity = motor_command.velocity_rpm
                await self._check_velocity_limits(motor_name, velocity)
                await self._check_temperature_limits(motor_name)
            except ValueError:
                raise SafetyViolationError(
                    f"Invalid motor name: {motor_name_str}",
                    "invalid_motor_name"
                )
            await self._check_operation_time_limits(motor_name, velocity)
        
        # Check for simultaneous motor conflicts
        await self._check_motor_conflicts(commands)
        
        return True
    
    async def update_motor_temperature(self, motor_name: MotorName, temperature: float) -> None:
        """Update motor temperature reading."""
        self._motor_temperatures[motor_name] = temperature
        max_temp = 85.0  # Default temperature limit
        
        if temperature > max_temp:
            await self._create_alert(
                SafetyLevel.CRITICAL,
                f"Motor {motor_name.value} temperature {temperature}°C exceeds limit {max_temp}°C",
                motor_name,
                "overtemperature"
            )
    
    async def start_motor_timing(self, motor_name: MotorName) -> None:
        """Start timing motor operation."""
        self._motor_last_start[motor_name] = datetime.now()
    
    async def stop_motor_timing(self, motor_name: MotorName) -> None:
        """Stop timing motor operation and update total runtime."""
        if self._motor_last_start[motor_name]:
            runtime = datetime.now() - self._motor_last_start[motor_name]
            self._motor_operation_time[motor_name] += runtime
            self._motor_last_start[motor_name] = None
    
    async def emergency_stop(self) -> None:
        """Activate emergency stop."""
        self._emergency_stop_active = True
        
        await self._create_alert(
            SafetyLevel.EMERGENCY,
            "Emergency stop activated - all motor operations halted",
            None,
            "emergency_stop"
        )
        
        # Stop timing for all motors
        for motor_name in MotorName:
            await self.stop_motor_timing(motor_name)
    
    async def reset_emergency_stop(self) -> None:
        """Reset emergency stop condition."""
        if not self._emergency_stop_active:
            return
        
        # Check if it's safe to reset
        critical_alerts = [
            alert for alert in self._active_alerts 
            if alert.level == SafetyLevel.CRITICAL and not alert.resolved
        ]
        
        if critical_alerts:
            raise SafetyViolationError(
                f"Cannot reset emergency stop - {len(critical_alerts)} critical alerts active",
                "unresolved_critical_alerts"
            )
        
        self._emergency_stop_active = False
        
        await self._create_alert(
            SafetyLevel.NORMAL,
            "Emergency stop reset - normal operations can resume",
            None,
            "emergency_stop_reset"
        )
    
    async def get_active_alerts(self) -> List[SafetyAlert]:
        """Get all active safety alerts."""
        return [alert for alert in self._active_alerts if not alert.resolved]
    
    async def resolve_alert(self, alert_index: int) -> None:
        """Mark a safety alert as resolved."""
        if 0 <= alert_index < len(self._active_alerts):
            self._active_alerts[alert_index].resolved = True
    
    async def get_motor_operation_time(self, motor_name: MotorName) -> timedelta:
        """Get total operation time for a motor."""
        total_time = self._motor_operation_time[motor_name]
        
        # Add current session time if motor is running
        if self._motor_last_start[motor_name]:
            current_session = datetime.now() - self._motor_last_start[motor_name]
            total_time += current_session
        
        return total_time
    
    @property
    def emergency_stop_active(self) -> bool:
        """Check if emergency stop is active."""
        return self._emergency_stop_active
    
    @property
    def system_status(self) -> SafetyLevel:
        """Get overall system safety status."""
        if self._emergency_stop_active:
            return SafetyLevel.EMERGENCY
        
        active_alerts = [alert for alert in self._active_alerts if not alert.resolved]
        
        if any(alert.level == SafetyLevel.CRITICAL for alert in active_alerts):
            return SafetyLevel.CRITICAL
        elif any(alert.level == SafetyLevel.WARNING for alert in active_alerts):
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
    
    async def _check_velocity_limits(self, motor_name: MotorName, velocity: float) -> None:
        """Check if velocity is within safety limits."""
        if not self.safety_limits.validate_rpm(motor_name, velocity):
            max_limit = self.safety_limits.get_limit_for_motor(motor_name)
            raise SafetyViolationError(
                f"Motor {motor_name.value} velocity {velocity} exceeds maximum {max_limit} RPM",
                "velocity_exceeded",
                motor_name
            )
        
        if velocity < 0:
            raise SafetyViolationError(
                f"Motor {motor_name.value} velocity {velocity} is negative",
                "negative_velocity",
                motor_name
            )
    
    async def _check_temperature_limits(self, motor_name: MotorName) -> None:
        """Check motor temperature limits."""
        if motor_name in self._motor_temperatures:
            temp = self._motor_temperatures[motor_name]
            max_temp = 85.0  # Default temperature limit
            
            if temp > max_temp:
                raise SafetyViolationError(
                    f"Motor {motor_name.value} temperature {temp}°C exceeds limit {max_temp}°C",
                    "overtemperature",
                    motor_name
                )
    
    async def _check_operation_time_limits(self, motor_name: MotorName, velocity: float) -> None:
        """Check motor operation time limits."""
        if velocity > 0:  # Motor will be running
            total_time = await self.get_motor_operation_time(motor_name)
            
            # Warning after 1 hour of continuous operation
            if total_time > timedelta(hours=1):
                await self._create_alert(
                    SafetyLevel.WARNING,
                    f"Motor {motor_name.value} has been running for {total_time}",
                    motor_name,
                    "extended_operation"
                )
            
            # Critical after 2 hours
            if total_time > timedelta(hours=2):
                await self._create_alert(
                    SafetyLevel.CRITICAL,
                    f"Motor {motor_name.value} extended operation time {total_time} - consider maintenance",
                    motor_name,
                    "excessive_operation_time"
                )
    
    async def _check_motor_conflicts(self, commands: MotorVelocityCommands) -> None:
        """Check for potentially conflicting motor operations."""
        # Example: High pen elevation with high canvas velocity might cause issues
        if (commands.pen_elevation_velocity_rpm > 20.0 and 
            commands.canvas_velocity_rpm > 25.0):
            
            await self._create_alert(
                SafetyLevel.WARNING,
                "High pen elevation and canvas velocity simultaneously - potential interference",
                None,
                "motor_conflict"
            )
    
    async def _create_alert(
        self,
        level: SafetyLevel,
        message: str,
        motor_name: Optional[MotorName],
        violation_type: str
    ) -> None:
        """Create a new safety alert."""
        alert = SafetyAlert(
            level=level,
            message=message,
            motor_name=motor_name,
            timestamp=datetime.now(),
            violation_type=violation_type
        )
        
        self._active_alerts.append(alert)
        
        # Log alert
        if level == SafetyLevel.EMERGENCY:
            self.logger.error(f"EMERGENCY: {message}")
        elif level == SafetyLevel.CRITICAL:
            self.logger.error(f"CRITICAL: {message}")
        elif level == SafetyLevel.WARNING:
            self.logger.warning(f"WARNING: {message}")
        else:
            self.logger.info(f"INFO: {message}")
        
        # Trigger emergency stop for critical issues
        if level == SafetyLevel.CRITICAL and not self._emergency_stop_active:
            if violation_type in ["velocity_exceeded", "overtemperature"]:
                await self.emergency_stop()