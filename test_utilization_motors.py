#!/usr/bin/env python3
"""
Test Utilization-Based Motor Logic
Test the new linear RPM mapping system
"""

import asyncio
from datetime import datetime

async def test_utilization_motors():
    """Test the new utilization-based motor logic with various scenarios."""
    
    from cloud.data_aggregator.motor_command_generator import MotorCommandGenerator
    from shared.models.blockchain_data import EthereumDataSnapshot, DataQuality, ApiResponseTimes
    
    generator = MotorCommandGenerator()
    
    print("UTILIZATION-BASED MOTOR TESTING")
    print("=" * 60)
    print("Configuration:")
    print(f"  Target: {generator.config['utilization_target_percent']:.1f}% (0 RPM)")
    print(f"  Max CW: {generator.config['utilization_max_cw_rpm']:.1f} RPM at 100%")
    print(f"  Max CCW: {generator.config['utilization_max_ccw_rpm']:.1f} RPM at 0%")
    print()
    
    # Test scenarios
    test_scenarios = [
        {"blob": 0.0, "block": 0.0, "description": "Minimum utilization"},
        {"blob": 25.0, "block": 25.0, "description": "Low utilization"},
        {"blob": 50.0, "block": 50.0, "description": "Target utilization"},
        {"blob": 75.0, "block": 75.0, "description": "High utilization"},
        {"blob": 100.0, "block": 100.0, "description": "Maximum utilization"},
        {"blob": 30.0, "block": 28.5, "description": "Current live data"},
    ]
    
    print("SCENARIO TESTING:")
    print("Blob%  Block%  Description              Color Depth Motor    Pen Elevation Motor")
    print("-" * 80)
    
    for scenario in test_scenarios:
        blob_util = scenario["blob"]
        block_util = scenario["block"]
        desc = scenario["description"]
        
        # Test individual motor calculations
        color_rpm, color_dir = generator._calculate_utilization_based_motor(blob_util)
        pen_rpm, pen_dir = generator._calculate_utilization_based_motor(block_util)
        
        color_dir_str = "CW" if color_dir.value == "clockwise" else "CCW"
        pen_dir_str = "CW" if pen_dir.value == "clockwise" else "CCW"
        
        print(f"{blob_util:5.1f}  {block_util:5.1f}   {desc:23} {color_rpm:4.1f} RPM {color_dir_str:3}      {pen_rpm:4.1f} RPM {pen_dir_str:3}")
    
    print()
    print("EXPECTED BEHAVIOR:")
    print("- At 0%: 2.0 RPM CCW (maximum deviation from target)")
    print("- At 50%: 0.0 RPM (at target, no motion)")  
    print("- At 100%: 10.0 RPM CW (maximum above target)")
    print("- Linear interpolation between these points")
    
    # Test full system with current data
    print("\nFULL SYSTEM TEST WITH CURRENT LIVE DATA:")
    test_data = EthereumDataSnapshot(
        timestamp=datetime.now().timestamp(),
        epoch=388407,
        eth_price_usd=4747.86,
        gas_price_gwei=0.3,
        blob_space_utilization_percent=30.0,  # Should be 0.8 RPM CCW
        block_fullness_percent=28.5,          # Should be 0.86 RPM CCW
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
    
    commands = await generator.generate_commands(test_data, test_data.epoch)
    
    print("\nFULL MOTOR COMMANDS:")
    for motor_name, command in commands.motors.items():
        dir_str = "CW" if command.direction.value == "clockwise" else "CCW"
        print(f"  {motor_name}: {command.velocity_rpm:.2f} RPM {dir_str}")

if __name__ == "__main__":
    asyncio.run(test_utilization_motors())