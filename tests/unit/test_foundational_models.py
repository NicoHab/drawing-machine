"""
Comprehensive test suite for Drawing Machine foundational models.

Tests all three core model modules: blockchain_data, motor_commands, and drawing_session.
Validates model creation, validation, serialization, and integration between components.
"""

import json
from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

# Import all model modules
from shared.models.blockchain_data import (
    EXAMPLE_SCHEMA,
    HIGH_ACTIVITY_EXAMPLE,
    ActivityLevel,
    ApiResponseTimes,
    DataQuality,
    EthereumDataSnapshot,
    MarketCondition,
)
from shared.models.drawing_session import (
    BLOCKCHAIN_SESSION_EXAMPLE,
    MANUAL_SESSION_EXAMPLE,
    BlockchainModeConfig,
    ControlSensitivity,
    DrawingMode,
    DrawingSession,
    DrawingSessionConfig,
    DrawingSessionError,
    ManualModeConfig,
    OfflineModeConfig,
    PlaybackSpeed,
    SessionStatistics,
    SessionStatus,
)
from shared.models.motor_commands import (
    EMERGENCY_STOP_EXAMPLE,
    EXAMPLE_MOTOR_COMMANDS,
    CommandExecutionStatus,
    MotorCommandError,
    MotorDirection,
    MotorName,
    MotorSafetyLimits,
    MotorState,
    MotorVelocityCommands,
    SingleMotorCommand,
)


class TestFixtures:
    """Test data fixtures for model testing."""

    @pytest.fixture
    def valid_api_response_times(self) -> dict[str, float]:
        """Valid API response times data."""
        return {
            "coinbase_ms": 150.5,
            "ethereum_rpc_ms": 220.1,
            "beacon_chain_ms": 180.3,
        }

    @pytest.fixture
    def valid_data_quality(self) -> dict[str, Any]:
        """Valid data quality data."""
        return {
            "price_data_fresh": True,
            "gas_data_fresh": True,
            "blob_data_fresh": True,
            "block_data_fresh": False,
            "overall_quality_score": 0.85,
        }

    @pytest.fixture
    def valid_ethereum_data(
        self, valid_data_quality, valid_api_response_times
    ) -> dict[str, Any]:
        """Valid Ethereum data snapshot."""
        return {
            "timestamp": datetime.now().timestamp(),
            "epoch": 1337,
            "eth_price_usd": 2500.50,
            "gas_price_gwei": 25.5,
            "blob_space_utilization_percent": 75.2,
            "block_fullness_percent": 85.7,
            "data_quality": valid_data_quality,
            "api_response_times": valid_api_response_times,
        }

    @pytest.fixture
    def valid_motor_command(self) -> dict[str, Any]:
        """Valid single motor command."""
        return {"velocity_rpm": 45.5, "direction": "CW"}

    @pytest.fixture
    def valid_motor_commands_data(self, valid_ethereum_data) -> dict[str, Any]:
        """Valid motor velocity commands data."""
        return {
            "timestamp": datetime.now().timestamp(),
            "epoch": 1337,
            "command_duration_seconds": 3.4,
            "motors": {
                "motor_canvas": {"velocity_rpm": 45.5, "direction": "CW"},
                "motor_pb": {"velocity_rpm": -25.2, "direction": "CCW"},
                "motor_pcd": {"velocity_rpm": 15.8, "direction": "CW"},
                "motor_pe": {"velocity_rpm": -35.1, "direction": "CCW"},
            },
            "source_data": valid_ethereum_data,
            "calculation_metadata": {
                "algorithm_version": "1.0.0",
                "calculation_time_ms": 12.5,
                "safety_checks_passed": True,
            },
        }

    @pytest.fixture
    def valid_session_config(self) -> dict[str, Any]:
        """Valid drawing session configuration."""
        return {
            "mode": "blockchain",
            "duration_minutes": 89.25,
            "blockchain_config": {
                "data_refresh_interval_seconds": 12.0,
                "quality_threshold": 0.7,
                "gas_tracking_enabled": True,
                "blob_tracking_enabled": True,
            },
        }

    @pytest.fixture
    def temp_sequence_file(self, tmp_path) -> str:
        """Create a temporary sequence file for offline mode testing."""
        sequence_file = tmp_path / "test_sequence.json"
        sequence_data = {
            "version": "1.0",
            "epochs": [
                {
                    "epoch": 1,
                    "commands": {
                        "motor_canvas": {"velocity_rpm": 10, "direction": "CW"}
                    },
                },
                {
                    "epoch": 2,
                    "commands": {
                        "motor_canvas": {"velocity_rpm": 20, "direction": "CW"}
                    },
                },
            ],
        }
        sequence_file.write_text(json.dumps(sequence_data))
        return str(sequence_file)


class TestEthereumDataSnapshot(TestFixtures):
    """Test suite for EthereumDataSnapshot model."""

    def test_create_valid_ethereum_data(self, valid_ethereum_data):
        """Test creating valid Ethereum data snapshot."""
        snapshot = EthereumDataSnapshot(**valid_ethereum_data)

        assert snapshot.epoch == 1337
        assert snapshot.eth_price_usd == 2500.50
        assert snapshot.gas_price_gwei == 25.5
        assert snapshot.blob_space_utilization_percent == 75.2
        assert snapshot.block_fullness_percent == 85.7
        assert isinstance(snapshot.data_quality, DataQuality)
        assert isinstance(snapshot.api_response_times, ApiResponseTimes)

    def test_ethereum_data_computed_fields(self, valid_ethereum_data):
        """Test computed fields for Ethereum data."""
        snapshot = EthereumDataSnapshot(**valid_ethereum_data)

        # Test datetime ISO conversion
        assert isinstance(snapshot.datetime_iso, str)
        assert "T" in snapshot.datetime_iso  # ISO format includes 'T'

        # Test high activity detection (should be False with current values)
        assert not snapshot.is_high_activity_epoch

        # Test motor control values
        motor_values = snapshot.get_motor_control_values()
        assert "canvas_motor" in motor_values
        assert "motor_pb" in motor_values
        assert "motor_pcd" in motor_values
        assert "motor_pe" in motor_values

        # All values should be between 0 and 1
        for value in motor_values.values():
            assert 0 <= value <= 1

    def test_high_activity_epoch_detection(self):
        """Test high activity epoch detection."""
        high_activity_data = {
            "timestamp": datetime.now().timestamp(),
            "epoch": 800,
            "eth_price_usd": 4200.00,
            "gas_price_gwei": 150.0,  # > 50
            "blob_space_utilization_percent": 95.0,  # > 60
            "block_fullness_percent": 98.5,  # > 80
            "data_quality": {
                "price_data_fresh": True,
                "gas_data_fresh": True,
                "blob_data_fresh": True,
                "block_data_fresh": True,
                "overall_quality_score": 0.95,
            },
            "api_response_times": {
                "coinbase_ms": 100.0,
                "ethereum_rpc_ms": 120.0,
                "beacon_chain_ms": 110.0,
            },
        }

        snapshot = EthereumDataSnapshot(**high_activity_data)
        assert snapshot.is_high_activity_epoch

    def test_market_condition_detection(self, valid_ethereum_data):
        """Test market condition classification."""
        snapshot = EthereumDataSnapshot(**valid_ethereum_data)
        condition = snapshot.get_market_condition()
        assert condition in [
            MarketCondition.BEAR,
            MarketCondition.BULL,
            MarketCondition.SIDEWAYS,
            MarketCondition.VOLATILE,
        ]

    def test_activity_level_detection(self, valid_ethereum_data):
        """Test activity level classification."""
        snapshot = EthereumDataSnapshot(**valid_ethereum_data)
        activity = snapshot.get_activity_level()
        assert activity in [
            ActivityLevel.LOW,
            ActivityLevel.MODERATE,
            ActivityLevel.HIGH,
            ActivityLevel.EXTREME,
        ]

    def test_data_quality_validation(self, valid_ethereum_data):
        """Test data quality validation."""
        snapshot = EthereumDataSnapshot(**valid_ethereum_data)
        assert isinstance(snapshot.is_valid_for_drawing(), bool)

    def test_ethereum_data_validation_errors(self):
        """Test validation errors for invalid Ethereum data."""
        # Test invalid epoch (too high)
        with pytest.raises(ValidationError):
            EthereumDataSnapshot(
                timestamp=datetime.now().timestamp(),
                epoch=2000,  # > 1574
                eth_price_usd=2500,
                gas_price_gwei=25,
                blob_space_utilization_percent=75,
                block_fullness_percent=85,
                data_quality={
                    "price_data_fresh": True,
                    "gas_data_fresh": True,
                    "blob_data_fresh": True,
                    "block_data_fresh": True,
                    "overall_quality_score": 0.8,
                },
                api_response_times={
                    "coinbase_ms": 100,
                    "ethereum_rpc_ms": 100,
                    "beacon_chain_ms": 100,
                },
            )

        # Test invalid ETH price (too low)
        with pytest.raises(ValidationError):
            EthereumDataSnapshot(
                timestamp=datetime.now().timestamp(),
                epoch=1000,
                eth_price_usd=50,  # < 100
                gas_price_gwei=25,
                blob_space_utilization_percent=75,
                block_fullness_percent=85,
                data_quality={
                    "price_data_fresh": True,
                    "gas_data_fresh": True,
                    "blob_data_fresh": True,
                    "block_data_fresh": True,
                    "overall_quality_score": 0.8,
                },
                api_response_times={
                    "coinbase_ms": 100,
                    "ethereum_rpc_ms": 100,
                    "beacon_chain_ms": 100,
                },
            )

    def test_api_response_times_computed_fields(self, valid_api_response_times):
        """Test ApiResponseTimes computed fields."""
        api_times = ApiResponseTimes(**valid_api_response_times)

        # Test average calculation
        expected_avg = (150.5 + 220.1 + 180.3) / 3
        assert abs(api_times.average_response_time - expected_avg) < 0.01

        # Test health check (all < 5000ms)
        assert api_times.is_healthy

    def test_data_quality_computed_fields(self, valid_data_quality):
        """Test DataQuality computed fields."""
        quality = DataQuality(**valid_data_quality)

        # Test freshness score (3 out of 4 fresh)
        assert quality.freshness_score == pytest.approx(0.75)

        # Test acceptable quality (0.85 > 0.7)
        assert quality.is_acceptable_quality


class TestMotorCommands(TestFixtures):
    """Test suite for motor command models."""

    def test_create_motor_safety_limits(self):
        """Test creating motor safety limits."""
        limits = MotorSafetyLimits()

        assert limits.motor_canvas_max_rpm == 120.0
        assert limits.motor_pb_max_rpm == 80.0
        assert limits.motor_pcd_max_rpm == 60.0
        assert limits.motor_pe_max_rpm == 90.0
        assert limits.emergency_stop_rpm == 0.0

    def test_motor_safety_limits_validation(self):
        """Test motor safety limits validation methods."""
        limits = MotorSafetyLimits()

        # Test valid RPM
        assert limits.validate_rpm(MotorName.CANVAS, 100.0)
        assert limits.validate_rpm(MotorName.PEN_BRUSH, -50.0)

        # Test invalid RPM (exceeds limit)
        assert not limits.validate_rpm(MotorName.CANVAS, 150.0)
        assert not limits.validate_rpm(MotorName.PEN_BRUSH, 100.0)

    def test_create_single_motor_command(self, valid_motor_command):
        """Test creating single motor command."""
        command = SingleMotorCommand(**valid_motor_command)

        assert command.velocity_rpm == 45.5
        assert command.direction == MotorDirection.CLOCKWISE
        assert command.absolute_velocity_rpm == 45.5

    def test_motor_state_creation(self):
        """Test creating motor state."""
        state_data = {
            "motor_name": "motor_canvas",
            "current_velocity_rpm": 45.0,
            "current_direction": "CW",
            "target_velocity_rpm": 50.0,
            "target_direction": "CW",
            "is_enabled": True,
            "last_command_timestamp": datetime.now().timestamp(),
            "temperature_celsius": 35.0,
        }

        state = MotorState(**state_data)
        assert state.motor_name == MotorName.CANVAS
        assert state.velocity_error_rpm == 5.0  # 50 - 45
        assert not state.is_at_target  # 5 RPM difference is > 5% of 50
        assert not state.is_overheating  # 35°C < 70°C

    def test_motor_velocity_commands_creation(self, valid_motor_commands_data):
        """Test creating motor velocity commands."""
        commands = MotorVelocityCommands(**valid_motor_commands_data)

        assert commands.epoch == 1337
        assert commands.command_duration_seconds == 3.4
        assert len(commands.motors) == 4
        assert all(
            motor_name in commands.motors
            for motor_name in ["motor_canvas", "motor_pb", "motor_pcd", "motor_pe"]
        )
        assert isinstance(commands.source_data, EthereumDataSnapshot)

    def test_motor_commands_computed_fields(self, valid_motor_commands_data):
        """Test computed fields for motor commands."""
        commands = MotorVelocityCommands(**valid_motor_commands_data)

        # Test emergency stop detection
        assert not commands.is_emergency_stop

        # Test power estimation
        assert commands.total_power_estimate > 0

        # Test complexity score
        assert 0 <= commands.command_complexity_score <= 1

    def test_motor_commands_safety_validation(self, valid_motor_commands_data):
        """Test safety validation for motor commands."""
        # Modify to exceed safety limits
        valid_motor_commands_data["motors"]["motor_canvas"][
            "velocity_rpm"
        ] = 150.0  # Exceeds 120 limit

        with pytest.raises(MotorCommandError):
            MotorVelocityCommands(**valid_motor_commands_data)

    def test_motor_commands_missing_motor_validation(self, valid_motor_commands_data):
        """Test validation for missing required motors."""
        # Remove required motor
        del valid_motor_commands_data["motors"]["motor_canvas"]

        with pytest.raises(MotorCommandError):
            MotorVelocityCommands(**valid_motor_commands_data)

    def test_motor_commands_safety_override(self, valid_motor_commands_data):
        """Test safety override functionality."""
        # Set velocity that exceeds limits
        valid_motor_commands_data["motors"]["motor_canvas"]["velocity_rpm"] = 150.0

        # Create with custom safety limits that allow this
        custom_limits = MotorSafetyLimits(motor_canvas_max_rpm=190.0)
        valid_motor_commands_data["safety_limits"] = custom_limits

        commands = MotorVelocityCommands(**valid_motor_commands_data)
        safe_commands = commands.apply_safety_override()

        # Should clamp to safety limit
        assert safe_commands.motors["motor_canvas"].velocity_rpm <= 190.0

    def test_motor_commands_execution_format(self, valid_motor_commands_data):
        """Test conversion to execution format."""
        commands = MotorVelocityCommands(**valid_motor_commands_data)
        exec_format = commands.to_execution_format()

        assert isinstance(exec_format, dict)
        for motor_name in ["motor_canvas", "motor_pb", "motor_pcd", "motor_pe"]:
            assert motor_name in exec_format
            assert "velocity_rpm" in exec_format[motor_name]
            assert "direction" in exec_format[motor_name]
            assert "duration_seconds" in exec_format[motor_name]

    def test_command_execution_status(self):
        """Test command execution status tracking."""
        status = CommandExecutionStatus(
            execution_success=True, execution_latency_ms=50, motor_responses=[]
        )

        assert status.execution_success
        assert status.execution_latency_ms == 50
        assert status.execution_quality_score > 0.6  # Should get bonus for low latency

    def test_emergency_stop_commands(self, valid_motor_commands_data):
        """Test emergency stop command detection."""
        # Set all motors to 0 RPM
        for motor in valid_motor_commands_data["motors"].values():
            motor["velocity_rpm"] = 0.0

        commands = MotorVelocityCommands(**valid_motor_commands_data)
        assert commands.is_emergency_stop


class TestDrawingSession(TestFixtures):
    """Test suite for drawing session models."""

    def test_create_blockchain_mode_config(self):
        """Test creating blockchain mode configuration."""
        config = BlockchainModeConfig()

        assert config.data_refresh_interval_seconds == 12.0
        assert config.quality_threshold == pytest.approx(0.7)
        assert config.gas_tracking_enabled
        assert config.blob_tracking_enabled
        assert config.total_epoch_duration_minutes > 0

    def test_create_manual_mode_config(self):
        """Test creating manual mode configuration."""
        config = ManualModeConfig()

        assert config.control_sensitivity == ControlSensitivity.MEDIUM
        assert config.velocity_scaling_factor == 1.0
        assert config.record_session
        assert config.sensitivity_multiplier == 1.0  # Medium * 1.0

    def test_create_offline_mode_config(self, temp_sequence_file):
        """Test creating offline mode configuration."""
        config = OfflineModeConfig(sequence_file_path=temp_sequence_file)

        assert config.sequence_file_path == temp_sequence_file
        assert config.playback_speed == PlaybackSpeed.NORMAL
        assert config.speed_multiplier == 1.0
        assert not config.loop_playback

    def test_offline_mode_config_invalid_file(self):
        """Test offline mode config with invalid file path."""
        with pytest.raises(DrawingSessionError):
            OfflineModeConfig(sequence_file_path="/nonexistent/file.json")

    def test_drawing_session_config_creation(self, valid_session_config):
        """Test creating drawing session configuration."""
        config = DrawingSessionConfig(**valid_session_config)

        assert config.mode == DrawingMode.BLOCKCHAIN
        assert config.duration_minutes == 89.25
        assert isinstance(config.blockchain_config, BlockchainModeConfig)
        assert config.estimated_epochs > 0
        assert config.end_time is not None

    def test_drawing_session_config_mode_validation(self):
        """Test mode-specific configuration validation."""
        # Test blockchain mode gets default config
        config = DrawingSessionConfig(mode=DrawingMode.BLOCKCHAIN)
        assert config.blockchain_config is not None

        # Test manual mode gets default config
        config = DrawingSessionConfig(mode=DrawingMode.MANUAL)
        assert config.manual_config is not None

        # Test offline mode requires config
        with pytest.raises(DrawingSessionError):
            DrawingSessionConfig(mode=DrawingMode.OFFLINE)

    def test_drawing_session_creation(self, valid_session_config):
        """Test creating drawing session."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        assert session.current_epoch == 0
        assert session.epochs_completed == 0
        assert session.status == SessionStatus.CREATED
        assert not session.is_active
        assert session.progress_percentage == pytest.approx(0.0)

    def test_drawing_session_lifecycle(self, valid_session_config):
        """Test drawing session lifecycle management."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        # Test session start
        assert session.start_session()
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active

        # Test session pause
        assert session.pause_session()
        assert session.status == SessionStatus.PAUSED
        assert not session.is_active

        # Test session resume
        assert session.resume_session()
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active

        # Test session stop
        assert session.stop_session()
        assert session.status == SessionStatus.COMPLETED
        assert not session.is_active

    def test_drawing_session_epoch_advancement(
        self, valid_session_config, valid_motor_commands_data
    ):
        """Test epoch advancement in drawing session."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config, total_epochs=10)

        # Start session
        session.start_session()

        # Create motor commands
        commands = MotorVelocityCommands(**valid_motor_commands_data)

        # Advance epochs
        for i in range(5):
            assert session.advance_epoch(commands)
            assert session.current_epoch == i + 1
            assert session.epochs_completed == i + 1

        # Check progress
        assert session.progress_percentage == pytest.approx(50.0)  # 5/10 epochs

    def test_drawing_session_mode_switching(self, valid_session_config):
        """Test mode switching during session."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        # Start in blockchain mode
        session.start_session()
        assert session.config.mode == DrawingMode.BLOCKCHAIN

        # Switch to hybrid mode (allowed)
        assert session.switch_mode(DrawingMode.HYBRID)
        assert session.config.mode == DrawingMode.HYBRID

        # Switch to manual mode from hybrid (allowed)
        assert session.switch_mode(DrawingMode.MANUAL)
        assert session.config.mode == DrawingMode.MANUAL

        # Try to switch to offline mode (not allowed)
        assert not session.switch_mode(DrawingMode.OFFLINE)
        assert session.config.mode == DrawingMode.MANUAL  # Should remain unchanged

    def test_session_statistics_tracking(self):
        """Test session statistics tracking."""
        stats = SessionStatistics()

        # Add some command results
        stats.add_command_result(True, 50.0)
        stats.add_command_result(True, 75.0)
        stats.add_command_result(False, 200.0)

        assert stats.total_commands_sent == 3
        assert stats.successful_commands == 2
        assert stats.failed_commands == 1
        assert stats.command_success_rate == 2 / 3
        assert stats.average_command_latency_ms == (50 + 75 + 200) / 3

        # Test data quality tracking
        stats.add_data_quality_score(0.8)
        stats.add_data_quality_score(0.9)
        assert stats.average_data_quality == pytest.approx(0.85)

        # Test health score calculation
        health_score = stats.get_session_health_score()
        assert 0 <= health_score <= 1

    def test_session_error_logging(self, valid_session_config):
        """Test session error logging."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        # Add some errors
        session.add_error("Test error 1")
        session.add_error("Test error 2")

        assert len(session.error_log) == 2
        assert "Test error 1" in session.error_log[0]
        assert "Test error 2" in session.error_log[1]

    def test_session_health_summary(self, valid_session_config):
        """Test session health summary generation."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        summary = session.get_session_health_summary()

        assert "health_score" in summary
        assert "status" in summary
        assert "progress_percent" in summary
        assert "command_success_rate" in summary
        assert "average_data_quality" in summary
        assert "safety_overrides" in summary


class TestModelIntegration(TestFixtures):
    """Test suite for model integration and serialization."""

    def test_json_serialization_ethereum_data(self, valid_ethereum_data):
        """Test JSON serialization of Ethereum data."""
        snapshot = EthereumDataSnapshot(**valid_ethereum_data)

        # Test safe serialization
        json_str = snapshot.model_dump_json_safe()
        assert isinstance(json_str, str)

        # Test safe deserialization (round-trip)
        reconstructed = EthereumDataSnapshot.model_validate_json_safe(json_str)
        assert reconstructed.epoch == snapshot.epoch
        assert reconstructed.eth_price_usd == snapshot.eth_price_usd

        # Test that computed fields work on reconstructed object
        assert hasattr(reconstructed, "datetime_iso")
        assert hasattr(reconstructed, "is_high_activity_epoch")

    def test_json_serialization_motor_commands(self, valid_motor_commands_data):
        """Test JSON serialization of motor commands."""
        commands = MotorVelocityCommands(**valid_motor_commands_data)

        # Test safe serialization
        json_str = commands.model_dump_json_safe()
        assert isinstance(json_str, str)

        # Test safe deserialization (round-trip)
        reconstructed = MotorVelocityCommands.model_validate_json_safe(json_str)
        assert reconstructed.epoch == commands.epoch
        assert len(reconstructed.motors) == len(commands.motors)

        # Test that computed fields work on reconstructed object
        assert hasattr(reconstructed, "total_power_estimate")
        assert hasattr(reconstructed, "is_emergency_stop")

    def test_json_serialization_drawing_session(self, valid_session_config):
        """Test JSON serialization of drawing session."""
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        # Test safe serialization
        json_str = session.model_dump_json_safe()
        assert isinstance(json_str, str)

        # Test safe deserialization (round-trip)
        reconstructed = DrawingSession.model_validate_json_safe(json_str)
        assert reconstructed.config.mode == session.config.mode
        assert reconstructed.current_epoch == session.current_epoch

        # Test that computed fields work on reconstructed object
        assert hasattr(reconstructed, "progress_percentage")
        assert hasattr(reconstructed, "estimated_time_remaining_minutes")

    def test_comprehensive_json_round_trip(
        self, valid_ethereum_data, valid_motor_commands_data, valid_session_config
    ):
        """Test comprehensive JSON round-trip for all models."""
        # Test EthereumDataSnapshot
        eth_snapshot = EthereumDataSnapshot(**valid_ethereum_data)
        eth_json = eth_snapshot.model_dump_json_safe()
        eth_reconstructed = EthereumDataSnapshot.model_validate_json_safe(eth_json)
        assert eth_reconstructed.epoch == eth_snapshot.epoch
        assert eth_reconstructed.eth_price_usd == eth_snapshot.eth_price_usd
        assert (
            eth_reconstructed.data_quality.overall_quality_score
            == eth_snapshot.data_quality.overall_quality_score
        )

        # Test MotorVelocityCommands
        motor_commands = MotorVelocityCommands(**valid_motor_commands_data)
        motor_json = motor_commands.model_dump_json_safe()
        motor_reconstructed = MotorVelocityCommands.model_validate_json_safe(motor_json)
        assert motor_reconstructed.epoch == motor_commands.epoch
        assert len(motor_reconstructed.motors) == len(motor_commands.motors)

        # Test DrawingSession
        session_config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=session_config)
        session_json = session.model_dump_json_safe()
        session_reconstructed = DrawingSession.model_validate_json_safe(session_json)
        assert session_reconstructed.config.mode == session.config.mode
        assert session_reconstructed.total_epochs == session.total_epochs

        # Test nested models work properly
        assert isinstance(eth_reconstructed.data_quality, DataQuality)
        assert isinstance(eth_reconstructed.api_response_times, ApiResponseTimes)
        assert isinstance(motor_reconstructed.source_data, EthereumDataSnapshot)
        assert isinstance(session_reconstructed.config, DrawingSessionConfig)

    def test_model_integration_workflow(
        self, valid_ethereum_data, valid_motor_commands_data, valid_session_config
    ):
        """Test complete workflow integration between all models."""
        # Create Ethereum data
        eth_data = EthereumDataSnapshot(**valid_ethereum_data)

        # Create motor commands using the Ethereum data
        valid_motor_commands_data["source_data"] = eth_data
        motor_commands = MotorVelocityCommands(**valid_motor_commands_data)

        # Create drawing session
        config = DrawingSessionConfig(**valid_session_config)
        session = DrawingSession(config=config)

        # Start session and advance epoch
        session.start_session()
        session.update_blockchain_data(eth_data)
        session.advance_epoch(motor_commands)

        # Verify integration
        assert session.current_blockchain_data.epoch == eth_data.epoch
        assert session.current_motor_commands.epoch == motor_commands.epoch
        assert session.current_epoch == 1
        assert session.epochs_completed == 1

    def test_example_schemas_validation(self):
        """Test that all example schemas are valid."""
        # Update timestamps to current time to avoid validation errors
        current_timestamp = datetime.now().timestamp()

        # Test blockchain data examples with current timestamps
        example_schema_updated = EXAMPLE_SCHEMA.copy()
        example_schema_updated["timestamp"] = current_timestamp
        EthereumDataSnapshot(**example_schema_updated)

        high_activity_example_updated = HIGH_ACTIVITY_EXAMPLE.copy()
        high_activity_example_updated["timestamp"] = current_timestamp
        EthereumDataSnapshot(**high_activity_example_updated)

        # Test motor command examples with current timestamps
        import copy

        motor_commands_updated = copy.deepcopy(EXAMPLE_MOTOR_COMMANDS)
        motor_commands_updated["timestamp"] = current_timestamp
        # Update source_data timestamp if it exists
        if "source_data" in motor_commands_updated:
            motor_commands_updated["source_data"]["timestamp"] = current_timestamp
        MotorVelocityCommands(**motor_commands_updated)

        emergency_stop_updated = copy.deepcopy(EMERGENCY_STOP_EXAMPLE)
        emergency_stop_updated["timestamp"] = current_timestamp
        # EMERGENCY_STOP_EXAMPLE doesn't have source_data, so only update if it exists
        if "source_data" in emergency_stop_updated:
            emergency_stop_updated["source_data"]["timestamp"] = current_timestamp
        MotorVelocityCommands(**emergency_stop_updated)

        # Test session examples
        DrawingSessionConfig(**BLOCKCHAIN_SESSION_EXAMPLE)
        DrawingSessionConfig(**MANUAL_SESSION_EXAMPLE)
        # Note: OFFLINE_SESSION_EXAMPLE would need a real file path

    def test_edge_case_validations(self):
        """Test various edge cases and boundary conditions."""
        # Test minimum values
        min_eth_data = {
            "timestamp": datetime.now().timestamp(),
            "epoch": 0,
            "eth_price_usd": 100.0,  # Minimum
            "gas_price_gwei": 0.1,  # Minimum
            "blob_space_utilization_percent": 0.0,
            "block_fullness_percent": 0.0,
            "data_quality": {
                "price_data_fresh": False,
                "gas_data_fresh": False,
                "blob_data_fresh": False,
                "block_data_fresh": False,
                "overall_quality_score": 0.0,
            },
            "api_response_times": {
                "coinbase_ms": 0.0,
                "ethereum_rpc_ms": 0.0,
                "beacon_chain_ms": 0.0,
            },
        }
        snapshot = EthereumDataSnapshot(**min_eth_data)
        assert snapshot.eth_price_usd == 100.0

        # Test maximum values
        max_eth_data = min_eth_data.copy()
        max_eth_data.update(
            {
                "epoch": 1574,  # Maximum
                "eth_price_usd": 50000.0,  # Maximum
                "gas_price_gwei": 1000.0,  # Maximum
                "blob_space_utilization_percent": 100.0,
                "block_fullness_percent": 100.0,
                "data_quality": {
                    "price_data_fresh": True,
                    "gas_data_fresh": True,
                    "blob_data_fresh": True,
                    "block_data_fresh": True,
                    "overall_quality_score": 1.0,
                },
                "api_response_times": {
                    "coinbase_ms": 30000.0,
                    "ethereum_rpc_ms": 30000.0,
                    "beacon_chain_ms": 30000.0,
                },
            }
        )
        snapshot = EthereumDataSnapshot(**max_eth_data)
        assert snapshot.epoch == 1574
        assert snapshot.eth_price_usd == 50000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

