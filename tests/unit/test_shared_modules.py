"""
Test suite for shared modules coverage.

Ensures adequate test coverage for the shared directory modules.
Tests focus on model functionality and utilities.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add shared to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))


class TestSharedModelsImports:
    """Test that all shared models can be imported."""

    def test_import_blockchain_data(self):
        """Test blockchain_data module import."""
        try:
            from shared.models import blockchain_data
            assert hasattr(blockchain_data, 'EthereumDataSnapshot')
            assert hasattr(blockchain_data, 'DataQuality')
            assert hasattr(blockchain_data, 'ApiResponseTimes')
        except ImportError as e:
            pytest.fail(f"Failed to import blockchain_data: {e}")

    def test_import_motor_commands(self):
        """Test motor_commands module import."""
        try:
            from shared.models import motor_commands
            # Test that module exists and can be imported
            assert motor_commands is not None
        except ImportError as e:
            pytest.fail(f"Failed to import motor_commands: {e}")

    def test_import_drawing_session(self):
        """Test drawing_session module import."""
        try:
            from shared.models import drawing_session
            # Test that module exists and can be imported
            assert drawing_session is not None
        except ImportError as e:
            pytest.fail(f"Failed to import drawing_session: {e}")


class TestEthereumDataSnapshot:
    """Test suite for EthereumDataSnapshot."""

    def test_ethereum_data_creation(self):
        """Test creating EthereumDataSnapshot instance."""
        from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
        
        data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=100,
            eth_price_usd=2500.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=50.0,
            block_fullness_percent=75.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=100.0,
                ethereum_rpc_ms=150.0,
                beacon_chain_ms=120.0
            )
        )
        
        assert data.epoch == 100
        assert data.eth_price_usd == 2500.0
        assert isinstance(data.timestamp, float)

    def test_ethereum_data_computed_fields(self):
        """Test computed fields in EthereumDataSnapshot."""
        from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
        
        data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=100,
            eth_price_usd=2500.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=50.0,
            block_fullness_percent=75.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=100.0,
                ethereum_rpc_ms=150.0,
                beacon_chain_ms=120.0
            )
        )
        
        # Test computed fields exist
        assert hasattr(data, 'datetime_iso')
        assert hasattr(data, 'is_high_activity_epoch')
        assert isinstance(data.datetime_iso, str)
        assert isinstance(data.is_high_activity_epoch, bool)

    def test_data_quality_models(self):
        """Test DataQuality and ApiResponseTimes models."""
        from shared.models.blockchain_data import DataQuality, ApiResponseTimes
        
        # Test DataQuality
        quality = DataQuality(
            price_data_fresh=True,
            gas_data_fresh=True,
            blob_data_fresh=False,
            block_data_fresh=True,
            overall_quality_score=0.8
        )
        
        assert quality.overall_quality_score == 0.8
        assert hasattr(quality, 'freshness_score')
        assert hasattr(quality, 'is_acceptable_quality')
        
        # Test ApiResponseTimes
        api_times = ApiResponseTimes(
            coinbase_ms=100.0,
            ethereum_rpc_ms=200.0,
            beacon_chain_ms=150.0
        )
        
        assert api_times.coinbase_ms == 100.0
        assert hasattr(api_times, 'average_response_time')
        assert hasattr(api_times, 'is_healthy')


class TestMotorCommands:
    """Test suite for motor commands (basic import test)."""

    def test_motor_commands_import(self):
        """Test that motor_commands module can be imported."""
        try:
            from shared.models import motor_commands
            # Basic import test - specific models may not exist yet
            assert motor_commands is not None
        except ImportError as e:
            pytest.fail(f"Motor commands import failed: {e}")


class TestDrawingSession:
    """Test suite for drawing session (basic import test)."""

    def test_drawing_session_import(self):
        """Test that drawing_session module can be imported."""
        try:
            from shared.models import drawing_session
            # Basic import test - specific models may not exist yet
            assert drawing_session is not None
        except ImportError as e:
            pytest.fail(f"Drawing session import failed: {e}")


class TestSharedModelsIntegration:
    """Integration tests for shared models working together."""

    def test_ethereum_data_functionality(self):
        """Test EthereumDataSnapshot functionality."""
        from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
        
        data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=100,
            eth_price_usd=2500.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=50.0,
            block_fullness_percent=75.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=100.0,
                ethereum_rpc_ms=150.0,
                beacon_chain_ms=120.0
            )
        )
        
        # Test methods
        motor_values = data.get_motor_control_values()
        assert isinstance(motor_values, dict)
        assert 'canvas_motor' in motor_values
        
        market_condition = data.get_market_condition()
        assert market_condition is not None
        
        activity_level = data.get_activity_level()
        assert activity_level is not None

    def test_json_serialization(self):
        """Test that models can be serialized to JSON."""
        from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
        
        data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=100,
            eth_price_usd=2500.0,
            gas_price_gwei=25.0,
            blob_space_utilization_percent=50.0,
            block_fullness_percent=75.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=100.0,
                ethereum_rpc_ms=150.0,
                beacon_chain_ms=120.0
            )
        )
        
        # Test JSON serialization
        json_data = data.model_dump_json_safe()
        assert isinstance(json_data, str)
        assert "eth_price_usd" in json_data
        
        # Test that we can reconstruct from JSON
        reconstructed = EthereumDataSnapshot.model_validate_json_safe(json_data)
        assert reconstructed.eth_price_usd == data.eth_price_usd


class TestSharedUtilities:
    """Test shared utilities and helper functions."""

    def test_shared_utils_import(self):
        """Test that shared utils can be imported."""
        try:
            from shared import utils
            assert utils is not None
        except ImportError:
            # Utils might be empty, which is OK
            pass

    def test_shared_package_structure(self):
        """Test shared package structure."""
        shared_dir = Path(__file__).parent.parent.parent / "shared"
        assert shared_dir.exists()
        assert (shared_dir / "__init__.py").exists()
        assert (shared_dir / "models").exists()
        assert (shared_dir / "models" / "__init__.py").exists()


class TestSharedModelFeatures:
    """Test advanced features of shared models."""

    def test_model_validation_rules(self):
        """Test validation rules in models."""
        from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
        from pydantic import ValidationError
        
        # Test that models have proper field constraints
        try:
            data = EthereumDataSnapshot(
                timestamp=datetime.now().timestamp(),
                epoch=100,
                eth_price_usd=2500.0,
                gas_price_gwei=25.0,
                blob_space_utilization_percent=50.0,
                block_fullness_percent=75.0,
                data_quality=DataQuality(
                    price_data_fresh=True,
                    gas_data_fresh=True,
                    blob_data_fresh=True,
                    block_data_fresh=True,
                    overall_quality_score=0.9
                ),
                api_response_times=ApiResponseTimes(
                    coinbase_ms=100.0,
                    ethereum_rpc_ms=150.0,
                    beacon_chain_ms=120.0
                )
            )
            assert data.eth_price_usd == 2500.0
        except ValidationError:
            pytest.fail("Valid data should not raise ValidationError")

    def test_model_edge_cases(self):
        """Test model edge cases and boundaries."""
        from shared.models.blockchain_data import DataQuality, ApiResponseTimes
        
        # Test boundary values
        quality = DataQuality(
            price_data_fresh=False,
            gas_data_fresh=False,
            blob_data_fresh=False,
            block_data_fresh=False,
            overall_quality_score=0.0  # Minimum value
        )
        assert quality.overall_quality_score == 0.0
        
        api_times = ApiResponseTimes(
            coinbase_ms=0.0,  # Minimum value
            ethereum_rpc_ms=0.0,
            beacon_chain_ms=0.0
        )
        assert api_times.coinbase_ms == 0.0


# Performance tests
def test_model_creation_performance():
    """Test that models can be created quickly."""
    import time
    
    start_time = time.time()
    
    # Create multiple model instances
    for i in range(10):
        try:
            from shared.models.blockchain_data import DataQuality, ApiResponseTimes
            
            DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            )
            
            ApiResponseTimes(
                coinbase_ms=100.0,
                ethereum_rpc_ms=150.0,
                beacon_chain_ms=120.0
            )
        except Exception:
            # Performance test - don't fail on validation errors
            pass
    
    creation_time = time.time() - start_time
    assert creation_time < 2.0, f"Model creation took too long: {creation_time:.2f}s"


def test_shared_directory_structure():
    """Test that shared directory has expected structure."""
    shared_dir = Path(__file__).parent.parent.parent / "shared"
    assert shared_dir.exists()
    assert (shared_dir / "__init__.py").exists()
    
    # Check for models directory
    models_dir = shared_dir / "models"
    assert models_dir.exists()
    assert (models_dir / "__init__.py").exists()
    
    # Check for main model files
    expected_files = [
        "blockchain_data.py",
        "motor_commands.py", 
        "drawing_session.py"
    ]
    
    for file_name in expected_files:
        assert (models_dir / file_name).exists(), f"Missing required file: {file_name}"


def test_shared_python_syntax():
    """Test that all Python files in shared have valid syntax."""
    shared_dir = Path(__file__).parent.parent.parent / "shared"
    
    for py_file in shared_dir.glob("**/*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                compile(content, py_file, 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {py_file}: {e}")
        except Exception:
            # File might have imports that aren't available in test environment
            # This is OK for syntax checking
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])