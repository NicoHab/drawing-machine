"""
Pydantic models for motor control commands in the Drawing Machine system.

This module provides structured data models for controlling the four motors that drive
the drawing mechanism. Each motor corresponds to specific drawing parameters controlled
by Ethereum blockchain data.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator, computed_field, model_validator

from .blockchain_data import EthereumDataSnapshot


class MotorDirection(str, Enum):
    """Motor rotation direction enumeration."""
    CLOCKWISE = "CW"
    COUNTER_CLOCKWISE = "CCW"


class MotorName(str, Enum):
    """Enumeration of motor names in the drawing machine."""
    CANVAS = "motor_canvas"
    PEN_BRUSH = "motor_pb"
    PEN_COLOR_DEPTH = "motor_pcd"
    PEN_ELEVATION = "motor_pe"


class MotorCommandError(Exception):
    """Custom exception for motor command validation and execution errors."""
    
    def __init__(self, message: str, motor_name: Optional[str] = None, command_value: Optional[float] = None):
        self.motor_name = motor_name
        self.command_value = command_value
        super().__init__(message)


class MotorSafetyLimits(BaseModel):
    """
    Safety limits for motor operations to prevent hardware damage.
    
    Defines maximum RPM limits for each motor based on hardware specifications
    and operational safety requirements.
    """
    
    motor_canvas_max_rpm: float = Field(
        default=120.0,
        ge=0,
        le=200.0,
        description="Maximum RPM for canvas rotation motor (0-200)"
    )
    
    motor_pb_max_rpm: float = Field(
        default=80.0,
        ge=0,
        le=150.0,
        description="Maximum RPM for pen brush pressure motor (0-150)"
    )
    
    motor_pcd_max_rpm: float = Field(
        default=60.0,
        ge=0,
        le=100.0,
        description="Maximum RPM for pen color depth motor (0-100)"
    )
    
    motor_pe_max_rpm: float = Field(
        default=90.0,
        ge=0,
        le=120.0,
        description="Maximum RPM for pen elevation motor (0-120)"
    )
    
    emergency_stop_rpm: float = Field(
        default=0.0,
        description="RPM value for emergency stop (always 0.0)"
    )
    
    def get_limit_for_motor(self, motor_name: MotorName) -> float:
        """Get the RPM limit for a specific motor."""
        limits_map = {
            MotorName.CANVAS: self.motor_canvas_max_rpm,
            MotorName.PEN_BRUSH: self.motor_pb_max_rpm,
            MotorName.PEN_COLOR_DEPTH: self.motor_pcd_max_rpm,
            MotorName.PEN_ELEVATION: self.motor_pe_max_rpm
        }
        return limits_map[motor_name]
    
    def validate_rpm(self, motor_name: MotorName, rpm: float) -> bool:
        """Validate if RPM is within safety limits for the given motor."""
        max_limit = self.get_limit_for_motor(motor_name)
        return 0 <= abs(rpm) <= max_limit
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }


class MotorState(BaseModel):
    """
    Current state and status of an individual motor.
    
    Tracks both current operational state and target state for motor control feedback.
    """
    
    motor_name: MotorName = Field(
        ...,
        description="Name identifier of the motor"
    )
    
    current_velocity_rpm: float = Field(
        ...,
        ge=-200.0,
        le=200.0,
        description="Current motor velocity in RPM (-200 to 200)"
    )
    
    current_direction: MotorDirection = Field(
        ...,
        description="Current motor rotation direction"
    )
    
    target_velocity_rpm: float = Field(
        ...,
        ge=-200.0,
        le=200.0,
        description="Target motor velocity in RPM (-200 to 200)"
    )
    
    target_direction: MotorDirection = Field(
        ...,
        description="Target motor rotation direction"
    )
    
    is_enabled: bool = Field(
        default=True,
        description="Whether the motor is enabled for operation"
    )
    
    last_command_timestamp: float = Field(
        ...,
        description="Unix timestamp of the last command sent to this motor"
    )
    
    temperature_celsius: Optional[float] = Field(
        default=None,
        ge=-40.0,
        le=100.0,
        description="Motor temperature in Celsius (-40 to 100)"
    )
    
    @computed_field
    @property
    def velocity_error_rpm(self) -> float:
        """Calculate the difference between target and current velocity."""
        return self.target_velocity_rpm - self.current_velocity_rpm
    
    @computed_field
    @property
    def is_at_target(self) -> bool:
        """Check if motor is at target velocity (within 5% tolerance)."""
        if self.target_velocity_rpm == 0:
            return abs(self.current_velocity_rpm) < 1.0
        tolerance = abs(self.target_velocity_rpm) * 0.05
        return abs(self.velocity_error_rpm) <= tolerance
    
    @computed_field
    @property
    def is_overheating(self) -> bool:
        """Check if motor temperature exceeds safe operating limits."""
        if self.temperature_celsius is None:
            return False
        return self.temperature_celsius > 70.0
    
    @computed_field
    @property
    def status_summary(self) -> str:
        """Generate human-readable status summary."""
        status_parts = []
        
        if not self.is_enabled:
            status_parts.append("DISABLED")
        elif self.is_overheating:
            status_parts.append("OVERHEATING")
        elif self.is_at_target:
            status_parts.append("AT_TARGET")
        else:
            status_parts.append("ADJUSTING")
            
        if self.current_velocity_rpm == 0:
            status_parts.append("STOPPED")
        
        return "_".join(status_parts)
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json
            data = std_json.loads(json_data)
        else:
            data = json_data
        
        computed_fields = {'velocity_error_rpm', 'is_at_target', 'is_overheating', 'status_summary'}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)
    
    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {'velocity_error_rpm', 'is_at_target', 'is_overheating', 'status_summary'}
        exclude = kwargs.get('exclude', set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class CommandExecutionStatus(BaseModel):
    """
    Status and results of motor command execution.
    
    Provides feedback on command success, timing, and individual motor responses.
    """
    
    command_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this command execution"
    )
    
    execution_success: bool = Field(
        ...,
        description="Whether the command executed successfully"
    )
    
    execution_latency_ms: int = Field(
        ...,
        ge=0,
        le=60000,
        description="Command execution latency in milliseconds (0-60000)"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    
    motor_responses: List[MotorState] = Field(
        default_factory=list,
        description="Individual motor state responses after command execution"
    )
    
    execution_timestamp: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Unix timestamp when command was executed"
    )
    
    @computed_field
    @property
    def all_motors_at_target(self) -> bool:
        """Check if all motors have reached their target states."""
        if not self.motor_responses:
            return False
        return all(motor.is_at_target for motor in self.motor_responses)
    
    @computed_field
    @property
    def any_motors_overheating(self) -> bool:
        """Check if any motors are overheating."""
        return any(motor.is_overheating for motor in self.motor_responses)
    
    @computed_field
    @property
    def execution_quality_score(self) -> float:
        """Calculate execution quality score (0.0-1.0) based on multiple factors."""
        if not self.execution_success:
            return 0.0
        
        # Base score for successful execution
        score = 0.6
        
        # Bonus for low latency (< 100ms gets full bonus)
        latency_bonus = max(0, (100 - self.execution_latency_ms) / 100) * 0.2
        score += latency_bonus
        
        # Bonus for motors reaching target
        if self.all_motors_at_target:
            score += 0.15
        
        # Penalty for overheating
        if self.any_motors_overheating:
            score -= 0.2
        
        # Bonus for having motor responses
        if self.motor_responses:
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def get_motor_state(self, motor_name: MotorName) -> Optional[MotorState]:
        """Get the state of a specific motor from the responses."""
        for motor_state in self.motor_responses:
            if motor_state.motor_name == motor_name:
                return motor_state
        return None
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that recursively excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json
            data = std_json.loads(json_data)
        else:
            data = json_data.copy() if isinstance(json_data, dict) else json_data
        
        # Filter root level computed fields
        root_computed_fields = {'all_motors_at_target', 'any_motors_overheating', 'execution_quality_score'}
        filtered_data = {k: v for k, v in data.items() if k not in root_computed_fields}
        
        # Filter nested motor_responses computed fields (MotorState objects)
        if 'motor_responses' in filtered_data and isinstance(filtered_data['motor_responses'], list):
            filtered_motor_responses = []
            for motor_state in filtered_data['motor_responses']:
                if isinstance(motor_state, dict):
                    motor_state_computed = {'velocity_error_rpm', 'is_at_target', 'is_overheating', 'status_summary'}
                    filtered_motor_state = {
                        k: v for k, v in motor_state.items() if k not in motor_state_computed
                    }
                    filtered_motor_responses.append(filtered_motor_state)
                else:
                    filtered_motor_responses.append(motor_state)
            filtered_data['motor_responses'] = filtered_motor_responses
        
        return cls.model_validate(filtered_data)
    
    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {'all_motors_at_target', 'any_motors_overheating', 'execution_quality_score'}
        exclude = kwargs.get('exclude', set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class SingleMotorCommand(BaseModel):
    """Command parameters for a single motor."""
    
    velocity_rpm: float = Field(
        ...,
        ge=-200.0,
        le=200.0,
        description="Target velocity in RPM (-200 to 200)"
    )
    
    direction: MotorDirection = Field(
        ...,
        description="Motor rotation direction (CW/CCW)"
    )
    
    @field_validator('velocity_rpm')
    @classmethod
    def validate_velocity_direction_consistency(cls, v: float, info) -> float:
        """Ensure velocity sign matches direction."""
        if hasattr(info, 'data') and 'direction' in info.data:
            direction = info.data['direction']
            if direction == MotorDirection.CLOCKWISE and v < 0:
                raise MotorCommandError(
                    "Clockwise direction requires positive velocity",
                    command_value=v
                )
            elif direction == MotorDirection.COUNTER_CLOCKWISE and v > 0:
                raise MotorCommandError(
                    "Counter-clockwise direction requires negative velocity", 
                    command_value=v
                )
        return v
    
    @computed_field
    @property
    def absolute_velocity_rpm(self) -> float:
        """Get absolute velocity value regardless of direction."""
        return abs(self.velocity_rpm)
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json
            data = std_json.loads(json_data)
        else:
            data = json_data
        
        computed_fields = {'absolute_velocity_rpm'}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)
    
    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {'absolute_velocity_rpm'}
        exclude = kwargs.get('exclude', set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class MotorVelocityCommands(BaseModel):
    """
    Complete motor velocity command set for the drawing machine.
    
    Contains synchronized commands for all four motors based on Ethereum blockchain data.
    Each motor controls a specific aspect of the drawing process.
    """
    
    timestamp: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Unix timestamp when commands were generated"
    )
    
    epoch: int = Field(
        ...,
        ge=0,
        le=1574,
        description="Drawing epoch number (0-1574)"
    )
    
    command_duration_seconds: float = Field(
        default=3.4,
        ge=0.1,
        le=60.0,
        description="Duration for which commands should be executed (0.1-60 seconds)"
    )
    
    motors: Dict[str, SingleMotorCommand] = Field(
        ...,
        description="Motor commands mapped by motor name"
    )
    
    source_data: EthereumDataSnapshot = Field(
        ...,
        description="Blockchain data snapshot used to generate these commands"
    )
    
    calculation_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about how commands were calculated"
    )
    
    safety_limits: MotorSafetyLimits = Field(
        default_factory=MotorSafetyLimits,
        description="Safety limits for motor operations"
    )
    
    command_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this command set"
    )
    
    @model_validator(mode='after')
    def validate_required_motors(self) -> 'MotorVelocityCommands':
        """Ensure all required motors are present in commands."""
        required_motors = {motor.value for motor in MotorName}
        provided_motors = set(self.motors.keys())
        
        missing_motors = required_motors - provided_motors
        if missing_motors:
            raise MotorCommandError(
                f"Missing required motors: {missing_motors}"
            )
        
        extra_motors = provided_motors - required_motors
        if extra_motors:
            raise MotorCommandError(
                f"Unknown motors provided: {extra_motors}"
            )
        
        return self
    
    @model_validator(mode='after')
    def validate_safety_limits(self) -> 'MotorVelocityCommands':
        """Validate all motor commands against safety limits."""
        for motor_name_str, command in self.motors.items():
            try:
                motor_name = MotorName(motor_name_str)
                if not self.safety_limits.validate_rpm(motor_name, command.velocity_rpm):
                    max_limit = self.safety_limits.get_limit_for_motor(motor_name)
                    raise MotorCommandError(
                        f"Velocity {command.velocity_rpm} exceeds safety limit {max_limit} for {motor_name_str}",
                        motor_name=motor_name_str,
                        command_value=command.velocity_rpm
                    )
            except ValueError:
                raise MotorCommandError(f"Invalid motor name: {motor_name_str}")
        
        return self
    
    @computed_field
    @property
    def total_power_estimate(self) -> float:
        """Estimate total power consumption based on motor velocities."""
        total_power = 0.0
        power_coefficients = {
            MotorName.CANVAS.value: 0.8,
            MotorName.PEN_BRUSH.value: 0.6,
            MotorName.PEN_COLOR_DEPTH.value: 0.4,
            MotorName.PEN_ELEVATION.value: 0.5
        }
        
        for motor_name, command in self.motors.items():
            coefficient = power_coefficients.get(motor_name, 0.5)
            motor_power = coefficient * abs(command.velocity_rpm) / 100
            total_power += motor_power
        
        return round(total_power, 2)
    
    @computed_field
    @property
    def is_emergency_stop(self) -> bool:
        """Check if this is an emergency stop command (all motors at 0 RPM)."""
        return all(command.velocity_rpm == 0 for command in self.motors.values())
    
    @computed_field
    @property
    def command_complexity_score(self) -> float:
        """Calculate command complexity score (0.0-1.0) based on motor coordination."""
        if self.is_emergency_stop:
            return 0.0
        
        # Calculate velocity variance for coordination complexity
        velocities = [abs(command.velocity_rpm) for command in self.motors.values()]
        avg_velocity = sum(velocities) / len(velocities)
        
        if avg_velocity == 0:
            return 0.0
        
        variance = sum((v - avg_velocity) ** 2 for v in velocities) / len(velocities)
        normalized_variance = min(1.0, variance / (avg_velocity ** 2))
        
        # Higher variance means more complex coordination
        return round(normalized_variance, 3)
    
    def get_motor_command(self, motor_name: MotorName) -> SingleMotorCommand:
        """Get command for a specific motor."""
        return self.motors[motor_name.value]
    
    def apply_safety_override(self) -> 'MotorVelocityCommands':
        """Apply safety overrides and return a new safe command set."""
        safe_motors = {}
        
        for motor_name_str, command in self.motors.items():
            motor_name = MotorName(motor_name_str)
            max_limit = self.safety_limits.get_limit_for_motor(motor_name)
            
            # Clamp velocity to safety limits
            safe_velocity = max(-max_limit, min(max_limit, command.velocity_rpm))
            
            # Adjust direction if velocity was clamped to opposite sign
            if safe_velocity * command.velocity_rpm < 0:
                new_direction = (MotorDirection.COUNTER_CLOCKWISE 
                               if command.direction == MotorDirection.CLOCKWISE 
                               else MotorDirection.CLOCKWISE)
            else:
                new_direction = command.direction
            
            safe_motors[motor_name_str] = SingleMotorCommand(
                velocity_rpm=safe_velocity,
                direction=new_direction
            )
        
        # Create new command set with safety overrides
        return MotorVelocityCommands(
            timestamp=self.timestamp,
            epoch=self.epoch,
            command_duration_seconds=self.command_duration_seconds,
            motors=safe_motors,
            source_data=self.source_data,
            calculation_metadata={
                **self.calculation_metadata,
                "safety_override_applied": True,
                "original_command_id": self.command_id
            },
            safety_limits=self.safety_limits
        )
    
    def to_execution_format(self) -> Dict[str, Dict[str, Union[float, str]]]:
        """Convert to format expected by motor control hardware."""
        return {
            motor_name: {
                "velocity_rpm": command.velocity_rpm,
                "direction": command.direction.value,
                "duration_seconds": self.command_duration_seconds
            }
            for motor_name, command in self.motors.items()
        }
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that recursively excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json
            data = std_json.loads(json_data)
        else:
            data = json_data.copy() if isinstance(json_data, dict) else json_data
        
        # Filter root level computed fields
        root_computed_fields = {'total_power_estimate', 'is_emergency_stop', 'command_complexity_score'}
        filtered_data = {k: v for k, v in data.items() if k not in root_computed_fields}
        
        # Filter nested source_data computed fields (EthereumDataSnapshot)
        if 'source_data' in filtered_data and isinstance(filtered_data['source_data'], dict):
            source_data = filtered_data['source_data']
            
            # Filter EthereumDataSnapshot computed fields
            eth_computed = {'datetime_iso', 'is_high_activity_epoch'}
            source_data = {k: v for k, v in source_data.items() if k not in eth_computed}
            
            # Filter nested data_quality computed fields
            if 'data_quality' in source_data and isinstance(source_data['data_quality'], dict):
                quality_computed = {'freshness_score', 'is_acceptable_quality'}
                source_data['data_quality'] = {
                    k: v for k, v in source_data['data_quality'].items() 
                    if k not in quality_computed
                }
            
            # Filter nested api_response_times computed fields
            if 'api_response_times' in source_data and isinstance(source_data['api_response_times'], dict):
                api_computed = {'average_response_time', 'is_healthy'}
                source_data['api_response_times'] = {
                    k: v for k, v in source_data['api_response_times'].items() 
                    if k not in api_computed
                }
            
            filtered_data['source_data'] = source_data
        
        # Filter nested motor objects computed fields (SingleMotorCommand)
        if 'motors' in filtered_data and isinstance(filtered_data['motors'], dict):
            for motor_name, motor_data in filtered_data['motors'].items():
                if isinstance(motor_data, dict):
                    motor_computed = {'absolute_velocity_rpm'}
                    filtered_data['motors'][motor_name] = {
                        k: v for k, v in motor_data.items() if k not in motor_computed
                    }
        
        return cls.model_validate(filtered_data)
    
    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {'total_power_estimate', 'is_emergency_stop', 'command_complexity_score'}
        exclude = kwargs.get('exclude', set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


# Example command schemas for documentation
EXAMPLE_MOTOR_COMMANDS = {
    "timestamp": 1692123456.789,
    "epoch": 1337,
    "command_duration_seconds": 3.4,
    "motors": {
        "motor_canvas": {
            "velocity_rpm": 45.5,
            "direction": "CW"
        },
        "motor_pb": {
            "velocity_rpm": -25.2,
            "direction": "CCW"
        },
        "motor_pcd": {
            "velocity_rpm": 15.8,
            "direction": "CW"
        },
        "motor_pe": {
            "velocity_rpm": -35.1,
            "direction": "CCW"
        }
    },
    "source_data": {
        "timestamp": 1692123456.789,
        "epoch": 1337,
        "eth_price_usd": 2500.50,
        "gas_price_gwei": 25.5,
        "blob_space_utilization_percent": 75.2,
        "block_fullness_percent": 85.7,
        "data_quality": {
            "price_data_fresh": True,
            "gas_data_fresh": True,
            "blob_data_fresh": True,
            "block_data_fresh": False,
            "overall_quality_score": 0.85
        },
        "api_response_times": {
            "coinbase_ms": 150.5,
            "ethereum_rpc_ms": 220.1,
            "beacon_chain_ms": 180.3
        }
    },
    "calculation_metadata": {
        "algorithm_version": "1.0.0",
        "calculation_time_ms": 12.5,
        "safety_checks_passed": True
    }
}

EMERGENCY_STOP_EXAMPLE = {
    "timestamp": 1692123456.789,
    "epoch": 1337,
    "command_duration_seconds": 0.1,
    "motors": {
        "motor_canvas": {"velocity_rpm": 0.0, "direction": "CW"},
        "motor_pb": {"velocity_rpm": 0.0, "direction": "CW"},
        "motor_pcd": {"velocity_rpm": 0.0, "direction": "CW"},
        "motor_pe": {"velocity_rpm": 0.0, "direction": "CW"}
    },
    "calculation_metadata": {
        "emergency_stop": True,
        "reason": "Data quality below threshold"
    }
}