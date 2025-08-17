"""
Multi-mode drawing session management models for the Drawing Machine system.

This module provides comprehensive session management for different drawing modes:
- BLOCKCHAIN: Live Ethereum data-driven drawing
- MANUAL: Human-controlled drawing operations
- OFFLINE: Pre-recorded sequence playback
- HYBRID: Combination of blockchain and manual control
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator

from .blockchain_data import EthereumDataSnapshot
from .motor_commands import MotorSafetyLimits, MotorVelocityCommands


class DrawingMode(str, Enum):
    """Drawing operation modes for the Drawing Machine."""

    BLOCKCHAIN = "blockchain"
    MANUAL = "manual"
    OFFLINE = "offline"
    HYBRID = "hybrid"


class SessionStatus(str, Enum):
    """Drawing session status enumeration."""

    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


class PlaybackSpeed(str, Enum):
    """Playback speed options for offline mode."""

    QUARTER = "0.25x"
    HALF = "0.5x"
    NORMAL = "1.0x"
    DOUBLE = "2.0x"
    QUADRUPLE = "4.0x"


class ControlSensitivity(str, Enum):
    """Manual control sensitivity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class DrawingSessionError(Exception):
    """Custom exception for drawing session errors."""

    def __init__(
        self,
        message: str,
        session_id: str | None = None,
        mode: DrawingMode | None = None,
    ):
        self.session_id = session_id
        self.mode = mode
        super().__init__(message)


class BlockchainModeConfig(BaseModel):
    """
    Configuration for blockchain-driven drawing mode.

    Defines API endpoints, data sources, and real-time blockchain data processing
    parameters for live Ethereum-driven drawing sessions.
    """

    ethereum_rpc_url: str = Field(
        default="https://eth-mainnet.g.alchemy.com/v2/",
        description="Ethereum RPC endpoint URL",
    )

    beacon_chain_api_url: str = Field(
        default="https://beaconcha.in/api/v1",
        description="Beacon Chain API endpoint URL",
    )

    coinbase_api_url: str = Field(
        default="https://api.coinbase.com/v2",
        description="Coinbase API endpoint URL for price data",
    )

    data_refresh_interval_seconds: float = Field(
        default=12.0,
        ge=1.0,
        le=60.0,
        description="Blockchain data refresh interval (1-60 seconds)",
    )

    price_update_interval_seconds: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="Price data update interval (5-300 seconds)",
    )

    gas_tracking_enabled: bool = Field(
        default=True, description="Enable gas price tracking for motor_pb control"
    )

    blob_tracking_enabled: bool = Field(
        default=True, description="Enable blob space tracking for motor_pcd control"
    )

    quality_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum data quality threshold (0.0-1.0)",
    )

    fallback_to_offline: bool = Field(
        default=True, description="Fall back to offline mode if data quality is poor"
    )

    api_timeout_seconds: float = Field(
        default=10.0, ge=1.0, le=30.0, description="API request timeout (1-30 seconds)"
    )

    @computed_field
    @property
    def total_epoch_duration_minutes(self) -> float:
        """Calculate total drawing duration for 1575 epochs at current refresh rate."""
        total_seconds = 1575 * self.data_refresh_interval_seconds
        return total_seconds / 60.0

    model_config = {"validate_assignment": True, "extra": "forbid"}

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data

        computed_fields = {"total_epoch_duration_minutes"}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"total_epoch_duration_minutes"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class ManualModeConfig(BaseModel):
    """
    Configuration for manual control drawing mode.

    Defines control sensitivity, recording settings, and human interface parameters
    for direct operator control of the drawing machine.
    """

    control_sensitivity: ControlSensitivity = Field(
        default=ControlSensitivity.MEDIUM, description="Control input sensitivity level"
    )

    velocity_scaling_factor: float = Field(
        default=1.0, ge=0.1, le=5.0, description="Velocity scaling multiplier (0.1-5.0)"
    )

    record_session: bool = Field(
        default=True, description="Record manual commands for later replay"
    )

    recording_file_path: str | None = Field(
        default=None, description="Path to save recorded session data"
    )

    enable_safety_overrides: bool = Field(
        default=True, description="Enable automatic safety limit enforcement"
    )

    command_rate_limit_hz: float = Field(
        default=10.0, ge=1.0, le=100.0, description="Maximum command rate in Hz (1-100)"
    )

    joystick_deadzone: float = Field(
        default=0.1, ge=0.0, le=0.5, description="Joystick input deadzone (0.0-0.5)"
    )

    enable_haptic_feedback: bool = Field(
        default=False, description="Enable haptic feedback for control devices"
    )

    @computed_field
    @property
    def sensitivity_multiplier(self) -> float:
        """Get velocity multiplier based on sensitivity setting."""
        multipliers = {
            ControlSensitivity.LOW: 0.5,
            ControlSensitivity.MEDIUM: 1.0,
            ControlSensitivity.HIGH: 1.5,
            ControlSensitivity.ULTRA: 2.0,
        }
        return multipliers[self.control_sensitivity] * self.velocity_scaling_factor

    model_config = {"validate_assignment": True, "extra": "forbid"}

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data

        computed_fields = {"sensitivity_multiplier"}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"sensitivity_multiplier"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class OfflineModeConfig(BaseModel):
    """
    Configuration for offline drawing sequence playback.

    Defines pre-recorded sequence file paths, playback settings, and timing
    parameters for reproducing previously recorded drawing sessions.
    """

    sequence_file_path: str = Field(
        ..., description="Path to the drawing sequence file"
    )

    playback_speed: PlaybackSpeed = Field(
        default=PlaybackSpeed.NORMAL, description="Playback speed multiplier"
    )

    loop_playback: bool = Field(
        default=False, description="Loop the sequence continuously"
    )

    start_from_epoch: int = Field(
        default=0, ge=0, description="Epoch number to start playback from"
    )

    end_at_epoch: int | None = Field(
        default=None,
        ge=0,
        description="Epoch number to end playback (None for full sequence)",
    )

    interpolate_missing_data: bool = Field(
        default=True, description="Interpolate motor commands for missing data points"
    )

    validate_sequence_integrity: bool = Field(
        default=True, description="Validate sequence file integrity before playback"
    )

    allow_speed_adjustment: bool = Field(
        default=True, description="Allow real-time speed adjustment during playback"
    )

    @field_validator("sequence_file_path")
    @classmethod
    def validate_sequence_file_exists(cls, v: str) -> str:
        """Validate that the sequence file exists and is readable."""
        path = Path(v)
        if not path.exists():
            raise DrawingSessionError(f"Sequence file not found: {v}")
        if not path.is_file():
            raise DrawingSessionError(f"Sequence path is not a file: {v}")
        return v

    @computed_field
    @property
    def speed_multiplier(self) -> float:
        """Get numeric speed multiplier from playback speed enum."""
        speed_map = {
            PlaybackSpeed.QUARTER: 0.25,
            PlaybackSpeed.HALF: 0.5,
            PlaybackSpeed.NORMAL: 1.0,
            PlaybackSpeed.DOUBLE: 2.0,
            PlaybackSpeed.QUADRUPLE: 4.0,
        }
        return speed_map[self.playback_speed]

    @computed_field
    @property
    def estimated_duration_minutes(self) -> float | None:
        """Estimate playback duration based on sequence length and speed."""
        # This would be calculated from actual sequence file analysis
        # For now, return None as placeholder
        return None

    model_config = {"validate_assignment": True, "extra": "forbid"}

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data

        computed_fields = {"speed_multiplier", "estimated_duration_minutes"}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"speed_multiplier", "estimated_duration_minutes"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class SessionStatistics(BaseModel):
    """
    Performance metrics and statistics for drawing sessions.

    Tracks various metrics during session execution including command counts,
    timing information, error rates, and quality measurements.
    """

    total_commands_sent: int = Field(
        default=0, ge=0, description="Total number of motor commands sent"
    )

    successful_commands: int = Field(
        default=0, ge=0, description="Number of successfully executed commands"
    )

    failed_commands: int = Field(
        default=0, ge=0, description="Number of failed command executions"
    )

    average_command_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Average command execution latency in milliseconds",
    )

    data_quality_scores: list[float] = Field(
        default_factory=list, description="Historical data quality scores"
    )

    api_response_times: list[float] = Field(
        default_factory=list,
        description="Historical API response times in milliseconds",
    )

    motor_temperature_readings: dict[str, list[float]] = Field(
        default_factory=dict, description="Motor temperature readings over time"
    )

    power_consumption_watts: list[float] = Field(
        default_factory=list, description="Power consumption readings in watts"
    )

    safety_overrides_triggered: int = Field(
        default=0, ge=0, description="Number of safety override interventions"
    )

    @computed_field
    @property
    def command_success_rate(self) -> float:
        """Calculate command execution success rate (0.0-1.0)."""
        if self.total_commands_sent == 0:
            return 0.0
        return self.successful_commands / self.total_commands_sent

    @computed_field
    @property
    def average_data_quality(self) -> float:
        """Calculate average data quality score."""
        if not self.data_quality_scores:
            return 0.0
        return sum(self.data_quality_scores) / len(self.data_quality_scores)

    @computed_field
    @property
    def average_api_response_time(self) -> float:
        """Calculate average API response time."""
        if not self.api_response_times:
            return 0.0
        return sum(self.api_response_times) / len(self.api_response_times)

    def get_session_health_score(self) -> float:
        """Calculate overall session health score (0.0-1.0)."""
        # Calculate command success rate directly
        command_success_rate = 0.0
        if self.total_commands_sent > 0:
            command_success_rate = self.successful_commands / self.total_commands_sent

        # Base score from command success rate
        health_score = command_success_rate * 0.4

        # Data quality contribution - calculate directly
        average_data_quality = 0.0
        if self.data_quality_scores:
            average_data_quality = sum(self.data_quality_scores) / len(
                self.data_quality_scores
            )

        if average_data_quality > 0:
            health_score += average_data_quality * 0.3

        # API performance contribution (< 1000ms is good) - calculate directly
        average_api_response_time = 0.0
        if self.api_response_times:
            average_api_response_time = sum(self.api_response_times) / len(
                self.api_response_times
            )

        if average_api_response_time > 0:
            api_score = max(0, (1000 - average_api_response_time) / 1000)
            health_score += api_score * 0.2

        # Safety penalty
        if self.total_commands_sent > 0:
            safety_ratio = self.safety_overrides_triggered / self.total_commands_sent
            health_score -= min(0.1, safety_ratio * 0.5)

        # Latency bonus (< 100ms gets bonus)
        if self.average_command_latency_ms > 0:
            latency_bonus = max(0, (100 - self.average_command_latency_ms) / 100) * 0.1
            health_score += latency_bonus

        return max(0.0, min(1.0, health_score))

    def add_command_result(self, success: bool, latency_ms: float) -> None:
        """Add a command execution result to statistics."""
        self.total_commands_sent += 1
        if success:
            self.successful_commands += 1
        else:
            self.failed_commands += 1

        # Update running average latency
        total_latency = self.average_command_latency_ms * (self.total_commands_sent - 1)
        self.average_command_latency_ms = (
            total_latency + latency_ms
        ) / self.total_commands_sent

    def add_data_quality_score(self, score: float) -> None:
        """Add a data quality measurement."""
        self.data_quality_scores.append(score)
        # Keep only last 100 scores to prevent unbounded growth
        if len(self.data_quality_scores) > 100:
            self.data_quality_scores = self.data_quality_scores[-100:]

    def add_api_response_time(self, response_time_ms: float) -> None:
        """Add an API response time measurement."""
        self.api_response_times.append(response_time_ms)
        # Keep only last 100 measurements
        if len(self.api_response_times) > 100:
            self.api_response_times = self.api_response_times[-100:]

    model_config = {"validate_assignment": True, "extra": "forbid"}

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data

        computed_fields = {
            "command_success_rate",
            "average_data_quality",
            "average_api_response_time",
        }
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {
            "command_success_rate",
            "average_data_quality",
            "average_api_response_time",
        }
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class DrawingSessionConfig(BaseModel):
    """
    Complete configuration for a drawing session.

    Encapsulates all mode-specific configurations and session parameters
    for different drawing operation modes.
    """

    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session identifier",
    )

    mode: DrawingMode = Field(..., description="Drawing operation mode")

    duration_minutes: float = Field(
        default=89.25,
        ge=0.1,
        le=1440.0,
        description="Session duration in minutes (0.1-1440)",
    )

    start_time: datetime = Field(
        default_factory=datetime.now, description="Session start time"
    )

    end_time: datetime | None = Field(
        default=None, description="Session end time (calculated from start + duration)"
    )

    blockchain_config: BlockchainModeConfig | None = Field(
        default=None, description="Blockchain mode configuration"
    )

    manual_config: ManualModeConfig | None = Field(
        default=None, description="Manual mode configuration"
    )

    offline_config: OfflineModeConfig | None = Field(
        default=None, description="Offline mode configuration"
    )

    hybrid_blockchain_weight: float | None = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Blockchain influence weight in hybrid mode (0.0-1.0)",
    )

    safety_limits: MotorSafetyLimits = Field(
        default_factory=MotorSafetyLimits,
        description="Motor safety limits for this session",
    )

    def model_post_init(self, __context) -> None:
        """Initialize configuration after model creation."""
        # Validate and set mode-specific configs
        if self.mode == DrawingMode.BLOCKCHAIN and not self.blockchain_config:
            self.blockchain_config = BlockchainModeConfig()
        elif self.mode == DrawingMode.MANUAL and not self.manual_config:
            self.manual_config = ManualModeConfig()
        elif self.mode == DrawingMode.OFFLINE and not self.offline_config:
            raise DrawingSessionError(
                "Offline mode requires offline_config",
                session_id=self.session_id,
                mode=self.mode,
            )
        elif self.mode == DrawingMode.HYBRID:
            if not self.blockchain_config:
                self.blockchain_config = BlockchainModeConfig()
            if not self.manual_config:
                self.manual_config = ManualModeConfig()

        # Calculate end time if not provided
        if not self.end_time:
            self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)

    @computed_field
    @property
    def estimated_epochs(self) -> int:
        """Estimate number of epochs based on mode and duration."""
        if self.mode == DrawingMode.BLOCKCHAIN and self.blockchain_config:
            # Calculate epochs based on refresh interval
            total_seconds = self.duration_minutes * 60
            return int(
                total_seconds / self.blockchain_config.data_refresh_interval_seconds
            )
        elif self.mode == DrawingMode.OFFLINE and self.offline_config:
            # Would be calculated from sequence file analysis
            return 1575  # Placeholder
        else:
            # For manual/hybrid, estimate based on typical command rate
            return int(self.duration_minutes * 10)  # ~10 commands per minute

    @computed_field
    @property
    def is_long_session(self) -> bool:
        """Check if this is considered a long drawing session (> 60 minutes)."""
        return self.duration_minutes > 60.0

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "arbitrary_types_allowed": False,
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
        computed_fields = {"estimated_epochs", "is_long_session"}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}

        # Filter nested blockchain_config computed fields
        if "blockchain_config" in filtered_data and isinstance(
            filtered_data["blockchain_config"], dict
        ):
            blockchain_computed = {"total_epoch_duration_minutes"}
            filtered_data["blockchain_config"] = {
                k: v
                for k, v in filtered_data["blockchain_config"].items()
                if k not in blockchain_computed
            }

        # Filter nested manual_config computed fields
        if "manual_config" in filtered_data and isinstance(
            filtered_data["manual_config"], dict
        ):
            manual_computed = {"sensitivity_multiplier"}
            filtered_data["manual_config"] = {
                k: v
                for k, v in filtered_data["manual_config"].items()
                if k not in manual_computed
            }

        # Filter nested offline_config computed fields
        if "offline_config" in filtered_data and isinstance(
            filtered_data["offline_config"], dict
        ):
            offline_computed = {"speed_multiplier", "estimated_duration_minutes"}
            filtered_data["offline_config"] = {
                k: v
                for k, v in filtered_data["offline_config"].items()
                if k not in offline_computed
            }

        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"estimated_epochs", "is_long_session"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class DrawingSession(BaseModel):
    """
    Active drawing session with real-time state management.

    Manages the execution of drawing sessions across different modes with
    progress tracking, motor command coordination, and session statistics.
    """

    config: DrawingSessionConfig = Field(..., description="Session configuration")

    current_epoch: int = Field(default=0, ge=0, description="Current epoch number")

    total_epochs: int = Field(
        default=1575, ge=1, description="Total epochs in this session"
    )

    epochs_completed: int = Field(
        default=0, ge=0, description="Number of completed epochs"
    )

    status: SessionStatus = Field(
        default=SessionStatus.CREATED, description="Current session status"
    )

    is_active: bool = Field(
        default=False, description="Whether session is actively running"
    )

    current_motor_commands: MotorVelocityCommands | None = Field(
        default=None, description="Current motor command set being executed"
    )

    current_blockchain_data: EthereumDataSnapshot | None = Field(
        default=None,
        description="Current blockchain data (for blockchain/hybrid modes)",
    )

    session_statistics: SessionStatistics = Field(
        default_factory=SessionStatistics, description="Session performance statistics"
    )

    error_log: list[str] = Field(
        default_factory=list, description="Session error messages"
    )

    last_update_timestamp: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Timestamp of last session update",
    )

    def model_post_init(self, __context) -> None:
        """Initialize total epochs after model creation."""
        # Calculate total epochs directly without accessing computed fields
        if self.total_epochs == 1575:  # Default value
            if (
                self.config.mode == DrawingMode.BLOCKCHAIN
                and self.config.blockchain_config
            ):
                total_seconds = self.config.duration_minutes * 60
                self.total_epochs = int(
                    total_seconds
                    / self.config.blockchain_config.data_refresh_interval_seconds
                )
            elif self.config.mode == DrawingMode.OFFLINE and self.config.offline_config:
                self.total_epochs = (
                    1575  # Placeholder - would be calculated from sequence file
                )
            else:
                # For manual/hybrid, estimate based on typical command rate
                self.total_epochs = int(self.config.duration_minutes * 10)

    @computed_field
    @property
    def progress_percentage(self) -> float:
        """Calculate session progress as percentage (0.0-100.0)."""
        if self.total_epochs == 0:
            return 0.0
        return (self.epochs_completed / self.total_epochs) * 100.0

    @computed_field
    @property
    def estimated_time_remaining_minutes(self) -> float:
        """Estimate remaining session time in minutes."""
        if self.total_epochs == 0 or self.epochs_completed >= self.total_epochs:
            return 0.0

        remaining_epochs = self.total_epochs - self.epochs_completed
        if self.config.mode == DrawingMode.BLOCKCHAIN and self.config.blockchain_config:
            remaining_seconds = (
                remaining_epochs
                * self.config.blockchain_config.data_refresh_interval_seconds
            )
            return remaining_seconds / 60.0
        else:
            # Fallback estimation
            progress_ratio = (
                self.epochs_completed / self.total_epochs
                if self.epochs_completed > 0
                else 0.1
            )
            elapsed_minutes = (
                datetime.now() - self.config.start_time
            ).total_seconds() / 60.0
            estimated_total_minutes = (
                elapsed_minutes / progress_ratio
                if progress_ratio > 0
                else self.config.duration_minutes
            )
            return max(0.0, estimated_total_minutes - elapsed_minutes)

    def get_session_health_summary(self) -> dict[str, str | float]:
        """Generate session health summary."""
        # Calculate progress percentage directly to avoid computed field recursion
        progress_percent = 0.0
        if self.total_epochs > 0:
            progress_percent = (self.epochs_completed / self.total_epochs) * 100.0

        return {
            "health_score": self.session_statistics.get_session_health_score(),
            "status": self.status.value,
            "progress_percent": progress_percent,
            "command_success_rate": (
                (
                    self.session_statistics.successful_commands
                    / self.session_statistics.total_commands_sent
                )
                if self.session_statistics.total_commands_sent > 0
                else 0.0
            ),
            "average_data_quality": (
                (
                    sum(self.session_statistics.data_quality_scores)
                    / len(self.session_statistics.data_quality_scores)
                )
                if self.session_statistics.data_quality_scores
                else 0.0
            ),
            "safety_overrides": self.session_statistics.safety_overrides_triggered,
        }

    def start_session(self) -> bool:
        """Start the drawing session."""
        if self.status != SessionStatus.CREATED:
            self.error_log.append(f"Cannot start session in {self.status} status")
            return False

        self.status = SessionStatus.INITIALIZING
        self.is_active = True
        self.config.start_time = datetime.now()
        self.config.end_time = self.config.start_time + timedelta(
            minutes=self.config.duration_minutes
        )
        self.last_update_timestamp = datetime.now().timestamp()

        # Mode-specific initialization
        try:
            if self.config.mode == DrawingMode.BLOCKCHAIN:
                self._initialize_blockchain_mode()
            elif self.config.mode == DrawingMode.MANUAL:
                self._initialize_manual_mode()
            elif self.config.mode == DrawingMode.OFFLINE:
                self._initialize_offline_mode()
            elif self.config.mode == DrawingMode.HYBRID:
                self._initialize_hybrid_mode()

            self.status = SessionStatus.ACTIVE
            return True

        except Exception as e:
            self.error_log.append(f"Initialization failed: {str(e)}")
            self.status = SessionStatus.FAILED
            self.is_active = False
            return False

    def pause_session(self) -> bool:
        """Pause the active session."""
        if self.status != SessionStatus.ACTIVE:
            return False

        self.status = SessionStatus.PAUSED
        self.is_active = False
        return True

    def resume_session(self) -> bool:
        """Resume a paused session."""
        if self.status != SessionStatus.PAUSED:
            return False

        self.status = SessionStatus.ACTIVE
        self.is_active = True
        return True

    def stop_session(self) -> bool:
        """Stop the session gracefully."""
        if self.status in [SessionStatus.COMPLETED, SessionStatus.FAILED]:
            return False

        self.status = SessionStatus.STOPPING
        self.is_active = False

        # Send emergency stop commands
        if self.current_motor_commands:
            self._send_emergency_stop()

        self.status = SessionStatus.COMPLETED
        return True

    def advance_epoch(
        self, motor_commands: MotorVelocityCommands | None = None
    ) -> bool:
        """Advance to the next epoch."""
        if not self.is_active or self.status != SessionStatus.ACTIVE:
            return False

        if self.epochs_completed >= self.total_epochs:
            self.stop_session()
            return False

        self.current_epoch += 1
        self.epochs_completed += 1
        self.current_motor_commands = motor_commands
        self.last_update_timestamp = datetime.now().timestamp()

        # Check if session should complete
        if self.epochs_completed >= self.total_epochs:
            self.stop_session()

        return True

    def update_blockchain_data(self, data: EthereumDataSnapshot) -> None:
        """Update current blockchain data for blockchain/hybrid modes."""
        if self.config.mode in [DrawingMode.BLOCKCHAIN, DrawingMode.HYBRID]:
            self.current_blockchain_data = data
            self.session_statistics.add_data_quality_score(
                data.data_quality.overall_quality_score
            )

    def add_error(self, error_message: str) -> None:
        """Add an error message to the session log."""
        timestamp = datetime.now().isoformat()
        self.error_log.append(f"[{timestamp}] {error_message}")

        # Keep only last 50 errors to prevent unbounded growth
        if len(self.error_log) > 50:
            self.error_log = self.error_log[-50:]

    def switch_mode(
        self, new_mode: DrawingMode, new_config: dict[str, Any] | None = None
    ) -> bool:
        """Switch drawing mode during session (if supported)."""
        if not self.is_active:
            return False

        # Only allow certain mode switches
        allowed_switches = {
            (DrawingMode.BLOCKCHAIN, DrawingMode.HYBRID),
            (DrawingMode.MANUAL, DrawingMode.HYBRID),
            (DrawingMode.HYBRID, DrawingMode.BLOCKCHAIN),
            (DrawingMode.HYBRID, DrawingMode.MANUAL),
        }

        if (self.config.mode, new_mode) not in allowed_switches:
            self.add_error(
                f"Mode switch from {self.config.mode} to {new_mode} not allowed"
            )
            return False

        try:
            self.config.mode = new_mode

            # Update configuration based on new mode
            if new_config:
                if (
                    new_mode == DrawingMode.BLOCKCHAIN
                    and "blockchain_config" in new_config
                ):
                    self.config.blockchain_config = BlockchainModeConfig(
                        **new_config["blockchain_config"]
                    )
                elif new_mode == DrawingMode.MANUAL and "manual_config" in new_config:
                    self.config.manual_config = ManualModeConfig(
                        **new_config["manual_config"]
                    )
                elif new_mode == DrawingMode.HYBRID:
                    if "blockchain_config" in new_config:
                        self.config.blockchain_config = BlockchainModeConfig(
                            **new_config["blockchain_config"]
                        )
                    if "manual_config" in new_config:
                        self.config.manual_config = ManualModeConfig(
                            **new_config["manual_config"]
                        )

            return True

        except Exception as e:
            self.add_error(f"Mode switch failed: {str(e)}")
            return False

    def _initialize_blockchain_mode(self) -> None:
        """Initialize blockchain mode specific settings."""
        if not self.config.blockchain_config:
            raise DrawingSessionError("Blockchain config required for blockchain mode")

    def _initialize_manual_mode(self) -> None:
        """Initialize manual mode specific settings."""
        if not self.config.manual_config:
            self.config.manual_config = ManualModeConfig()

    def _initialize_offline_mode(self) -> None:
        """Initialize offline mode specific settings."""
        if not self.config.offline_config:
            raise DrawingSessionError("Offline config required for offline mode")

        # Validate sequence file
        if not Path(self.config.offline_config.sequence_file_path).exists():
            raise DrawingSessionError(
                f"Sequence file not found: {self.config.offline_config.sequence_file_path}"
            )

    def _initialize_hybrid_mode(self) -> None:
        """Initialize hybrid mode specific settings."""
        if not self.config.blockchain_config:
            self.config.blockchain_config = BlockchainModeConfig()
        if not self.config.manual_config:
            self.config.manual_config = ManualModeConfig()

    def _send_emergency_stop(self) -> None:
        """Send emergency stop commands to all motors."""
        # This would interface with the motor control system
        # For now, just log the action
        self.add_error("Emergency stop commands sent to all motors")

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "arbitrary_types_allowed": False,
    }

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that recursively excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data.copy() if isinstance(json_data, dict) else json_data

        # Recursively filter computed fields from nested objects
        filtered_data = cls._filter_computed_fields_recursive(data)
        return cls.model_validate(filtered_data)

    @classmethod
    def _filter_computed_fields_recursive(cls, data):
        """Recursively filter computed fields from data structure."""
        if not isinstance(data, dict):
            return data

        # Root level computed fields for DrawingSession
        root_computed_fields = {
            "progress_percentage",
            "estimated_time_remaining_minutes",
        }

        # Filter root level computed fields
        filtered = {k: v for k, v in data.items() if k not in root_computed_fields}

        # Recursively process nested objects
        for key, value in filtered.items():
            if key == "config" and isinstance(value, dict):
                filtered[key] = cls._filter_config_computed_fields(value)
            elif key == "session_statistics" and isinstance(value, dict):
                filtered[key] = cls._filter_session_stats_computed_fields(value)
            elif isinstance(value, dict):
                filtered[key] = cls._filter_computed_fields_recursive(value)
            elif isinstance(value, list):
                filtered[key] = [
                    (
                        cls._filter_computed_fields_recursive(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]

        return filtered

    @classmethod
    def _filter_config_computed_fields(cls, config_data):
        """Filter computed fields from config object."""
        if not isinstance(config_data, dict):
            return config_data

        # Config level computed fields
        config_computed_fields = {"estimated_epochs", "is_long_session"}
        filtered_config = {
            k: v for k, v in config_data.items() if k not in config_computed_fields
        }

        # Filter blockchain_config computed fields
        if "blockchain_config" in filtered_config and isinstance(
            filtered_config["blockchain_config"], dict
        ):
            blockchain_computed = {"total_epoch_duration_minutes"}
            filtered_config["blockchain_config"] = {
                k: v
                for k, v in filtered_config["blockchain_config"].items()
                if k not in blockchain_computed
            }

        # Filter manual_config computed fields
        if "manual_config" in filtered_config and isinstance(
            filtered_config["manual_config"], dict
        ):
            manual_computed = {"sensitivity_multiplier"}
            filtered_config["manual_config"] = {
                k: v
                for k, v in filtered_config["manual_config"].items()
                if k not in manual_computed
            }

        # Filter offline_config computed fields
        if "offline_config" in filtered_config and isinstance(
            filtered_config["offline_config"], dict
        ):
            offline_computed = {"speed_multiplier", "estimated_duration_minutes"}
            filtered_config["offline_config"] = {
                k: v
                for k, v in filtered_config["offline_config"].items()
                if k not in offline_computed
            }

        return filtered_config

    @classmethod
    def _filter_session_stats_computed_fields(cls, stats_data):
        """Filter computed fields from session statistics object."""
        if not isinstance(stats_data, dict):
            return stats_data

        # Session statistics computed fields
        stats_computed_fields = {
            "command_success_rate",
            "average_data_quality",
            "average_api_response_time",
        }
        return {k: v for k, v in stats_data.items() if k not in stats_computed_fields}

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"progress_percentage", "estimated_time_remaining_minutes"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


# Example session configurations for documentation
BLOCKCHAIN_SESSION_EXAMPLE = {
    "mode": "blockchain",
    "duration_minutes": 89.25,
    "blockchain_config": {
        "data_refresh_interval_seconds": 12.0,
        "quality_threshold": 0.7,
        "gas_tracking_enabled": True,
        "blob_tracking_enabled": True,
    },
}

MANUAL_SESSION_EXAMPLE = {
    "mode": "manual",
    "duration_minutes": 30.0,
    "manual_config": {
        "control_sensitivity": "medium",
        "record_session": True,
        "enable_safety_overrides": True,
    },
}

OFFLINE_SESSION_EXAMPLE = {
    "mode": "offline",
    "duration_minutes": 45.0,
    "offline_config": {
        "sequence_file_path": "/data/sequences/ethereum_bull_run_2024.json",
        "playback_speed": "1.0x",
        "loop_playback": False,
    },
}

HYBRID_SESSION_EXAMPLE = {
    "mode": "hybrid",
    "duration_minutes": 60.0,
    "hybrid_blockchain_weight": 0.7,
    "blockchain_config": {"data_refresh_interval_seconds": 15.0},
    "manual_config": {"control_sensitivity": "high", "velocity_scaling_factor": 0.8},
}
