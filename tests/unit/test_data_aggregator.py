"""
Tests for cloud data aggregator components.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from cloud.data_aggregator import (
    BlockchainDataFetcher,
    DataProcessor,
    MotorCommandGenerator,
    FetchError,
    ProcessingError,
    GenerationError,
)
from shared.models.blockchain_data import (
    EthereumDataSnapshot,
    ApiResponseTimes,
    DataQuality,
    MarketCondition,
    ActivityLevel,
)
from shared.models.motor_commands import MotorSafetyLimits, MotorDirection, MotorName


class TestBlockchainDataFetcher:
    """Test blockchain data fetcher functionality."""
    
    def test_initialization(self):
        """Test blockchain data fetcher initialization."""
        fetcher = BlockchainDataFetcher()
        
        assert fetcher.coinbase_url is not None
        assert fetcher.ethereum_rpc_url is not None
        assert fetcher.beacon_chain_url is not None
        assert fetcher._fallback_data is not None
    
    @pytest.mark.asyncio
    async def test_fetch_current_data(self):
        """Test fetching current blockchain data."""
        fetcher = BlockchainDataFetcher()
        
        # Mock the individual fetch methods
        with patch.object(fetcher, '_fetch_coinbase_data', new_callable=AsyncMock) as mock_coinbase:
            with patch.object(fetcher, '_fetch_ethereum_rpc_data', new_callable=AsyncMock) as mock_ethereum:
                with patch.object(fetcher, '_fetch_beacon_chain_data', new_callable=AsyncMock) as mock_beacon:
                    
                    # Setup mock returns
                    mock_coinbase.return_value = {"eth_price_usd": 2500.0, "coinbase_available": True}
                    mock_ethereum.return_value = {"gas_price_gwei": 25.0, "blob_space_utilization_percent": 60.0, "block_fullness_percent": 80.0, "ethereum_rpc_available": True}
                    mock_beacon.return_value = {"beacon_participation_rate": 96.5, "eth_staked_percent": 28.0, "validator_count": 580000, "beacon_chain_available": True}
                    
                    # Test fetch
                    result = await fetcher.fetch_current_data()
                    
                    assert isinstance(result, EthereumDataSnapshot)
                    assert result.eth_price_usd == 2500.0
                    assert result.gas_price_gwei == 25.0
                    assert result.blob_space_utilization_percent == 60.0
                    assert result.block_fullness_percent == 80.0
                    assert result.data_quality.overall_quality_score > 0
    
    @pytest.mark.asyncio
    async def test_fallback_data(self):
        """Test fallback data creation when APIs fail."""
        fetcher = BlockchainDataFetcher()
        
        # Test fallback creation
        fallback = await fetcher._create_fallback_snapshot()
        
        assert isinstance(fallback, EthereumDataSnapshot)
        assert fallback.data_quality.overall_quality_score == 0.0  # Indicates fallback
        assert fallback.eth_price_usd == fetcher._fallback_data["eth_price_usd"]
    
    def test_market_condition_determination(self):
        """Test market condition classification."""
        fetcher = BlockchainDataFetcher()
        
        assert fetcher._determine_market_condition(1000) == MarketCondition.BEAR
        assert fetcher._determine_market_condition(2000) == MarketCondition.SIDEWAYS
        assert fetcher._determine_market_condition(3000) == MarketCondition.BULL
        assert fetcher._determine_market_condition(5000) == MarketCondition.VOLATILE
    
    def test_activity_level_determination(self):
        """Test network activity level classification."""
        fetcher = BlockchainDataFetcher()
        
        # Test LOW: (10/50) + (20/100) = 0.2 + 0.2 = 0.4 < 0.5
        assert fetcher._determine_activity_level(10, 20) == ActivityLevel.LOW
        # Test MODERATE: (10/50) + (30/100) = 0.2 + 0.3 = 0.5, but need < 1.0
        assert fetcher._determine_activity_level(10, 30) == ActivityLevel.MODERATE  
        # Test HIGH: (25/50) + (50/100) = 0.5 + 0.5 = 1.0 (>= 1.0, < 1.5)
        assert fetcher._determine_activity_level(25, 50) == ActivityLevel.HIGH
        # Test EXTREME: (100/50) + (90/100) = 2.0 + 0.9 = 2.9 >= 1.5
        assert fetcher._determine_activity_level(100, 90) == ActivityLevel.EXTREME


class TestMotorCommandGenerator:
    """Test motor command generator functionality."""
    
    def test_initialization(self):
        """Test motor command generator initialization."""
        generator = MotorCommandGenerator()
        
        assert generator.safety_limits is not None
        assert generator.config is not None
        assert "canvas_price_sensitivity" in generator.config
    
    @pytest.mark.asyncio
    async def test_generate_test_commands(self):
        """Test generating test commands with mock data."""
        generator = MotorCommandGenerator()
        
        commands = await generator.generate_test_commands(epoch=1)
        
        assert commands.epoch == 1
        assert len(commands.motors) == 4
        assert MotorName.CANVAS.value in commands.motors
        assert MotorName.PEN_BRUSH.value in commands.motors
        assert MotorName.PEN_COLOR_DEPTH.value in commands.motors
        assert MotorName.PEN_ELEVATION.value in commands.motors
    
    @pytest.mark.asyncio
    async def test_generate_canvas_command(self):
        """Test canvas motor command generation."""
        generator = MotorCommandGenerator()
        
        # Create mock blockchain data
        mock_data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=1337,
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
        
        command = await generator._generate_canvas_command(mock_data)
        
        assert command.velocity_rpm >= 0
        assert command.direction in [MotorDirection.CLOCKWISE, MotorDirection.COUNTER_CLOCKWISE]
    
    @pytest.mark.asyncio
    async def test_safety_limits_application(self):
        """Test that safety limits are properly applied."""
        # Create restrictive safety limits
        safety_limits = MotorSafetyLimits(
            motor_canvas_max_rpm=10.0,
            motor_pb_max_rpm=10.0,
            motor_pcd_max_rpm=10.0,
            motor_pe_max_rpm=10.0,
            emergency_stop_rpm=0.0,
        )
        
        generator = MotorCommandGenerator(safety_limits)
        
        # Generate commands that would exceed limits
        commands = await generator.generate_test_commands(epoch=1)
        
        # Check that all velocities are within safety limits
        for motor_name, command in commands.motors.items():
            motor_enum = MotorName(motor_name)
            max_limit = safety_limits.get_limit_for_motor(motor_enum)
            safety_margin = max_limit * (1.0 - generator.config["safety_margin_percent"])
            
            assert command.velocity_rpm <= safety_margin
    
    def test_config_update(self):
        """Test configuration updates."""
        generator = MotorCommandGenerator()
        
        original_sensitivity = generator.config["canvas_price_sensitivity"]
        new_config = {"canvas_price_sensitivity": 0.02}
        
        generator.update_config(new_config)
        
        assert generator.config["canvas_price_sensitivity"] == 0.02
        assert generator.config["canvas_price_sensitivity"] != original_sensitivity


class TestDataProcessor:
    """Test data processor functionality."""
    
    def test_initialization(self):
        """Test data processor initialization."""
        processor = DataProcessor()
        
        assert processor.fetcher is not None
        assert processor.generator is not None
        assert processor.stats is not None
        assert processor.stats["total_processed"] == 0
    
    @pytest.mark.asyncio
    async def test_process_current_data(self):
        """Test processing current data end-to-end."""
        processor = DataProcessor()
        
        # Mock the fetcher and generator
        with patch.object(processor.fetcher, 'fetch_current_data', new_callable=AsyncMock) as mock_fetch:
            with patch.object(processor.generator, 'generate_commands', new_callable=AsyncMock) as mock_generate:
                
                # Setup mock blockchain data
                mock_data = MagicMock(spec=EthereumDataSnapshot)
                mock_data.timestamp = datetime.now().timestamp()
                mock_fetch.return_value = mock_data
                
                # Setup mock commands
                mock_commands = MagicMock()
                mock_commands.epoch = 1
                mock_generate.return_value = mock_commands
                
                # Test processing
                result = await processor.process_current_data(epoch=1)
                
                assert result == mock_commands
                assert processor.stats["total_processed"] == 1
                assert processor.stats["successful_fetches"] == 1
                assert processor.stats["successful_generations"] == 1
    
    @pytest.mark.asyncio
    async def test_process_with_fetch_error(self):
        """Test processing when blockchain fetch fails."""
        processor = DataProcessor()
        
        # Mock fetcher to raise error
        with patch.object(processor.fetcher, 'fetch_current_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = FetchError("API unavailable", "coinbase", 500)
            
            # Test that processing raises ProcessingError
            with pytest.raises(ProcessingError) as exc_info:
                await processor.process_current_data(epoch=1)
            
            assert exc_info.value.stage == "process_current_data"
            assert processor.stats["failed_fetches"] > 0
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing of multiple epochs."""
        processor = DataProcessor()
        
        epochs = [1, 2, 3]
        
        # Mock the fetcher and generator
        with patch.object(processor.fetcher, 'fetch_current_data', new_callable=AsyncMock) as mock_fetch:
            with patch.object(processor.generator, 'generate_commands', new_callable=AsyncMock) as mock_generate:
                
                mock_data = MagicMock(spec=EthereumDataSnapshot)
                mock_fetch.return_value = mock_data
                
                mock_commands = MagicMock()
                mock_generate.return_value = mock_commands
                
                results = await processor.process_batch(epochs)
                
                assert len(results) == 3
                assert all(commands is not None for _, commands in results)
                assert mock_generate.call_count == 3
    
    def test_processing_status(self):
        """Test getting processing status."""
        processor = DataProcessor()
        
        status = processor.get_processing_status()
        
        assert "status" in status
        assert "statistics" in status
        assert "cache_status" in status
        assert "data_sources" in status
        assert "recent_errors" in status
    
    def test_cache_operations(self):
        """Test cache operations."""
        processor = DataProcessor()
        
        # Test cache clearing
        processor.clear_cache()
        assert len(processor._data_cache) == 0
        assert len(processor._command_cache) == 0
    
    def test_config_updates(self):
        """Test updating generator configuration."""
        processor = DataProcessor()
        
        new_config = {"canvas_price_sensitivity": 0.05}
        processor.update_generator_config(new_config)
        
        assert processor.generator.config["canvas_price_sensitivity"] == 0.05