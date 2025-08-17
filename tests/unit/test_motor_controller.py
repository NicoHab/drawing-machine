"""
Tests for motor controller edge components.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from edge.motor_controller import (
    HardwareInterface,
    MotorDriver,
    MotorDriverError,
    SafetyController,
    SafetyViolationError,
    ConnectionStatus,
    SafetyLevel,
)
from shared.models.motor_commands import (
    MotorDirection,
    MotorName,
    MotorSafetyLimits,
    MotorVelocityCommands,
    SingleMotorCommand,
)
from shared.models.blockchain_data import (
    EthereumDataSnapshot,
    ApiResponseTimes,
    DataQuality,
)


class TestMotorDriver:
    """Test motor driver functionality."""
    
    def test_initialization(self):
        """Test motor driver initialization."""
        driver = MotorDriver(host="localhost", port=8888)
        
        assert driver.host == "localhost"
        assert driver.port == 8888
        assert driver.connection_status == ConnectionStatus.DISCONNECTED
        assert not driver.is_connected
        assert driver.safety_limits is not None
    
    def test_default_safety_limits(self):
        """Test default safety limits creation."""
        driver = MotorDriver()
        limits = driver.safety_limits
        
        assert limits.motor_canvas_max_rpm == 35.0
        assert limits.motor_pb_max_rpm == 25.0
        assert limits.emergency_stop_rpm == 0.0
    
    @pytest.mark.asyncio
    async def test_motor_command_validation(self):
        """Test motor command validation."""
        driver = MotorDriver()
        
        # Create mock source data
        source_data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=1,
            eth_price_usd=3000.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=60.0,
            block_fullness_percent=80.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=150.0,
                ethereum_rpc_ms=200.0,
                beacon_chain_ms=180.0,
            ),
        )
        
        # Valid commands
        commands = MotorVelocityCommands(
            epoch=1,
            motors={
                MotorName.CANVAS.value: SingleMotorCommand(velocity_rpm=10.0, direction=MotorDirection.CLOCKWISE),
                MotorName.PEN_BRUSH.value: SingleMotorCommand(velocity_rpm=15.0, direction=MotorDirection.CLOCKWISE),
                MotorName.PEN_COLOR_DEPTH.value: SingleMotorCommand(velocity_rpm=20.0, direction=MotorDirection.COUNTER_CLOCKWISE),
                MotorName.PEN_ELEVATION.value: SingleMotorCommand(velocity_rpm=25.0, direction=MotorDirection.CLOCKWISE),
            },
            source_data=source_data,
        )
        
        # Should not raise exception
        driver._validate_commands(commands)
    
    @pytest.mark.asyncio
    async def test_velocity_limit_validation(self):
        """Test velocity limit validation."""
        driver = MotorDriver()
        
        # Create mock source data
        source_data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=1,
            eth_price_usd=3000.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=60.0,
            block_fullness_percent=80.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=150.0,
                ethereum_rpc_ms=200.0,
                beacon_chain_ms=180.0,
            ),
        )
        
        # Commands exceeding velocity limit
        commands = MotorVelocityCommands(
            epoch=1,
            motors={
                MotorName.CANVAS.value: SingleMotorCommand(velocity_rpm=50.0, direction=MotorDirection.CLOCKWISE),  # Exceeds default limit
                MotorName.PEN_BRUSH.value: SingleMotorCommand(velocity_rpm=15.0, direction=MotorDirection.CLOCKWISE),
                MotorName.PEN_COLOR_DEPTH.value: SingleMotorCommand(velocity_rpm=20.0, direction=MotorDirection.COUNTER_CLOCKWISE),
                MotorName.PEN_ELEVATION.value: SingleMotorCommand(velocity_rpm=25.0, direction=MotorDirection.CLOCKWISE),
            },
            source_data=source_data,
        )
        
        with pytest.raises(MotorDriverError, match="exceeds max limit"):
            driver._validate_commands(commands)


class TestSafetyController:
    """Test safety controller functionality."""
    
    def test_initialization(self):
        """Test safety controller initialization."""
        limits = MotorSafetyLimits(
            motor_canvas_max_rpm=30.0,
            motor_pb_max_rpm=25.0,
            motor_pcd_max_rpm=20.0,
            motor_pe_max_rpm=25.0,
            emergency_stop_rpm=0.0,
        )
        
        controller = SafetyController(limits)
        
        assert controller.safety_limits == limits
        assert controller.system_status == SafetyLevel.NORMAL
        assert not controller.emergency_stop_active
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """Test emergency stop functionality."""
        limits = MotorSafetyLimits(
            motor_canvas_max_rpm=30.0,
            motor_pb_max_rpm=25.0,
            motor_pcd_max_rpm=20.0,
            motor_pe_max_rpm=25.0,
            emergency_stop_rpm=0.0,
        )
        
        controller = SafetyController(limits)
        
        # Activate emergency stop
        await controller.emergency_stop()
        
        assert controller.emergency_stop_active
        assert controller.system_status == SafetyLevel.EMERGENCY
        
        # Get active alerts
        alerts = await controller.get_active_alerts()
        assert len(alerts) > 0
        assert alerts[0].level == SafetyLevel.EMERGENCY
    
    @pytest.mark.asyncio
    async def test_velocity_validation(self):
        """Test velocity validation."""
        limits = MotorSafetyLimits(
            motor_canvas_max_rpm=30.0,
            motor_pb_max_rpm=25.0,
            motor_pcd_max_rpm=20.0,
            motor_pe_max_rpm=25.0,
            emergency_stop_rpm=0.0,
        )
        
        controller = SafetyController(limits)
        
        # Create mock source data
        source_data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=1,
            eth_price_usd=3000.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=60.0,
            block_fullness_percent=80.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=150.0,
                ethereum_rpc_ms=200.0,
                beacon_chain_ms=180.0,
            ),
        )
        
        # Valid commands
        commands = MotorVelocityCommands(
            epoch=1,
            motors={
                MotorName.CANVAS.value: SingleMotorCommand(velocity_rpm=25.0, direction=MotorDirection.CLOCKWISE),
                MotorName.PEN_BRUSH.value: SingleMotorCommand(velocity_rpm=15.0, direction=MotorDirection.CLOCKWISE),
                MotorName.PEN_COLOR_DEPTH.value: SingleMotorCommand(velocity_rpm=20.0, direction=MotorDirection.COUNTER_CLOCKWISE),
                MotorName.PEN_ELEVATION.value: SingleMotorCommand(velocity_rpm=10.0, direction=MotorDirection.CLOCKWISE),
            },
            source_data=source_data,
        )
        
        # Should validate successfully
        result = await controller.validate_motor_commands(commands)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_velocity_limit_violation(self):
        """Test velocity limit violation detection."""
        limits = MotorSafetyLimits(
            motor_canvas_max_rpm=30.0,
            motor_pb_max_rpm=25.0,
            motor_pcd_max_rpm=20.0,
            motor_pe_max_rpm=25.0,
            emergency_stop_rpm=0.0,
        )
        
        controller = SafetyController(limits)
        
        # Create mock source data
        source_data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=1,
            eth_price_usd=3000.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=60.0,
            block_fullness_percent=80.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=150.0,
                ethereum_rpc_ms=200.0,
                beacon_chain_ms=180.0,
            ),
        )
        
        # Commands with velocity exceeding limit
        commands = MotorVelocityCommands(
            epoch=1,
            motors={
                MotorName.CANVAS.value: SingleMotorCommand(velocity_rpm=35.0, direction=MotorDirection.CLOCKWISE),  # Exceeds limit of 30.0
                MotorName.PEN_BRUSH.value: SingleMotorCommand(velocity_rpm=15.0, direction=MotorDirection.CLOCKWISE),
                MotorName.PEN_COLOR_DEPTH.value: SingleMotorCommand(velocity_rpm=20.0, direction=MotorDirection.COUNTER_CLOCKWISE),
                MotorName.PEN_ELEVATION.value: SingleMotorCommand(velocity_rpm=10.0, direction=MotorDirection.CLOCKWISE),
            },
            source_data=source_data,
        )
        
        with pytest.raises(SafetyViolationError, match="velocity.*exceeds maximum"):
            await controller.validate_motor_commands(commands)
    
    @pytest.mark.asyncio
    async def test_temperature_monitoring(self):
        """Test motor temperature monitoring."""
        limits = MotorSafetyLimits(
            motor_canvas_max_rpm=30.0,
            motor_pb_max_rpm=25.0,
            motor_pcd_max_rpm=20.0,
            motor_pe_max_rpm=25.0,
            emergency_stop_rpm=0.0,
        )
        
        controller = SafetyController(limits)
        
        # Update motor temperature within limits
        await controller.update_motor_temperature(MotorName.CANVAS, 70.0)
        
        # Update motor temperature exceeding limits
        await controller.update_motor_temperature(MotorName.CANVAS, 85.0)
        
        # Check for temperature alert
        alerts = await controller.get_active_alerts()
        temp_alerts = [alert for alert in alerts if alert.violation_type == "overtemperature"]
        assert len(temp_alerts) > 0
        assert temp_alerts[0].level == SafetyLevel.CRITICAL


class TestHardwareInterface:
    """Test hardware interface functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test hardware interface initialization."""
        with patch.object(MotorDriver, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            
            interface = HardwareInterface(host="localhost", port=8888)
            
            # Mock the background tasks to avoid actual network calls
            with patch.object(interface, '_start_background_tasks', new_callable=AsyncMock):
                result = await interface.initialize()
                
                assert result is True
                mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_motor_command_execution(self):
        """Test motor command execution through hardware interface."""
        interface = HardwareInterface()
        
        # Mock the motor driver methods
        with patch.object(interface.motor_driver, 'send_motor_commands', new_callable=AsyncMock) as mock_send:
            with patch.object(interface.safety_controller, 'validate_motor_commands', new_callable=AsyncMock) as mock_validate:
                mock_send.return_value = True
                mock_validate.return_value = True
                
                # Create mock source data
                source_data = EthereumDataSnapshot(
                    timestamp=datetime.now().timestamp(),
                    epoch=1,
                    eth_price_usd=3000.0,
                    gas_price_gwei=25.0,
                    blob_space_utilization_percent=60.0,
                    block_fullness_percent=80.0,
                    data_quality=DataQuality(
                        price_data_fresh=True,
                        gas_data_fresh=True,
                        blob_data_fresh=True,
                        block_data_fresh=True,
                        overall_quality_score=0.9
                    ),
                    api_response_times=ApiResponseTimes(
                        coinbase_ms=150.0,
                        ethereum_rpc_ms=200.0,
                        beacon_chain_ms=180.0,
                    ),
                )
                
                commands = MotorVelocityCommands(
                    epoch=1,
                    motors={
                        MotorName.CANVAS.value: SingleMotorCommand(velocity_rpm=10.0, direction=MotorDirection.CLOCKWISE),
                        MotorName.PEN_BRUSH.value: SingleMotorCommand(velocity_rpm=15.0, direction=MotorDirection.CLOCKWISE),
                        MotorName.PEN_COLOR_DEPTH.value: SingleMotorCommand(velocity_rpm=20.0, direction=MotorDirection.COUNTER_CLOCKWISE),
                        MotorName.PEN_ELEVATION.value: SingleMotorCommand(velocity_rpm=25.0, direction=MotorDirection.CLOCKWISE),
                    },
                    source_data=source_data,
                )
                
                result = await interface.execute_motor_commands(commands)
                
                assert result is True
                mock_validate.assert_called_once_with(commands)
                mock_send.assert_called_once_with(commands)
    
    @pytest.mark.asyncio
    async def test_emergency_stop_integration(self):
        """Test emergency stop through hardware interface."""
        interface = HardwareInterface()
        
        # Mock the emergency stop methods
        with patch.object(interface.safety_controller, 'emergency_stop', new_callable=AsyncMock) as mock_safety_stop:
            with patch.object(interface.motor_driver, 'emergency_stop', new_callable=AsyncMock) as mock_driver_stop:
                
                await interface.emergency_stop()
                
                mock_safety_stop.assert_called_once()
                mock_driver_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """Test system status reporting."""
        interface = HardwareInterface()
        
        # Mock the status methods
        mock_motor_statuses = {
            MotorName.CANVAS: MagicMock(
                current_velocity=10.0,
                target_velocity=10.0,
                direction=MotorDirection.CLOCKWISE,
                is_moving=True,
                last_command_time=datetime.now(),
                error_count=0,
                temperature=65.0,
            )
        }
        
        with patch.object(interface.motor_driver, 'get_all_motor_status', new_callable=AsyncMock) as mock_motor_status:
            with patch.object(interface.safety_controller, 'get_active_alerts', new_callable=AsyncMock) as mock_alerts:
                mock_motor_status.return_value = mock_motor_statuses
                mock_alerts.return_value = []
                
                status = await interface.get_system_status()
                
                assert "connection_status" in status
                assert "safety_level" in status
                assert "motor_statuses" in status
                assert "active_alerts" in status
                assert "statistics" in status