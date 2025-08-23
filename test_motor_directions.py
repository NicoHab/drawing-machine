#!/usr/bin/env python3
"""
Test Motor Direction Logic
Test the new 50% threshold direction rules
"""

import asyncio
from datetime import datetime

async def test_motor_directions():
    """Test motor direction logic with current blockchain data."""
    
    # Import after loading env vars
    from cloud.data_aggregator.motor_command_generator import MotorCommandGenerator
    from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
    
    generator = MotorCommandGenerator()
    
    # Create test data with current values
    test_data = EthereumDataSnapshot(
        timestamp=datetime.now().timestamp(),
        epoch=388406,
        eth_price_usd=4743.70,
        gas_price_gwei=0.3,
        blob_space_utilization_percent=30.0,  # Below 50% -> should be CCW
        block_fullness_percent=28.5,  # Below 50% -> should be CCW
        data_quality=DataQuality(
            price_data_fresh=True,
            gas_data_fresh=True,
            blob_data_fresh=True,
            block_data_fresh=True,
            overall_quality_score=0.8
        ),
        api_response_times=ApiResponseTimes(
            coinbase_ms=100.0,
            ethereum_rpc_ms=200.0,
            beacon_chain_ms=300.0
        )
    )
    
    print("MOTOR DIRECTION TEST")
    print("=" * 50)
    print(f"Blob Utilization: {test_data.blob_space_utilization_percent:.1f}% (should be CCW if < 50%)")
    print(f"Block Fullness: {test_data.block_fullness_percent:.1f}% (should be CCW if < 50%)")
    print()
    
    # Test individual motor commands
    color_depth_cmd = await generator._generate_color_depth_command(test_data)
    pen_elevation_cmd = await generator._generate_pen_elevation_command(test_data)
    
    print("EXPECTED vs ACTUAL DIRECTIONS:")
    print(f"Color Depth Motor (blob-based): Expected CCW, Got {color_depth_cmd.direction}")
    print(f"Pen Elevation Motor (block-based): Expected CCW, Got {pen_elevation_cmd.direction}")
    
    # Test full command generation
    print("\nFULL MOTOR COMMANDS:")
    commands = await generator.generate_commands(test_data, test_data.epoch)
    
    for motor_name, command in commands.motors.items():
        print(f"{motor_name}: {command.velocity_rpm:.1f} RPM {command.direction}")

if __name__ == "__main__":
    asyncio.run(test_motor_directions())