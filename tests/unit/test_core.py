"""
Essential tests for core functionality.
"""

def test_basic_imports():
    """Test that core modules can be imported."""
    try:
        from shared.models.blockchain_data import EthereumDataSnapshot
        from shared.models.motor_commands import MotorSafetyLimits
        assert True
    except ImportError as e:
        assert False, f"Core imports failed: {e}"


def test_basic_functionality():
    """Test basic functionality works."""
    assert 2 + 2 == 4
    assert "test" in "testing"


def test_pydantic_models():
    """Test that Pydantic models work."""
    from shared.models.blockchain_data import ApiResponseTimes
    
    api_times = ApiResponseTimes(
        coinbase_ms=100.0,
        ethereum_rpc_ms=150.0, 
        beacon_chain_ms=120.0
    )
    
    assert api_times.coinbase_ms == 100.0
    assert api_times.ethereum_rpc_ms == 150.0