#!/usr/bin/env python3
"""
Test Live Blockchain Data Integration
Test the fixed blockchain fetcher with real APIs
"""

import asyncio
import os
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    
load_env_file()

async def test_live_blockchain_fetcher():
    """Test the blockchain fetcher with live APIs."""
    print("Testing Live Blockchain Data Fetcher")
    print("=" * 50)
    
    # Import after loading env vars
    from cloud.data_aggregator.blockchain_fetcher import BlockchainDataFetcher
    
    fetcher = BlockchainDataFetcher()
    
    print(f"Using Etherscan API key: {os.getenv('ETHERSCAN_API_KEY', 'NOT_SET')[:10]}...")
    print()
    
    try:
        # Test the fixed fetcher
        print("Fetching live blockchain data...")
        snapshot = await fetcher.fetch_current_data()
        
        print(f"SUCCESS! Live blockchain data:")
        print(f"  ETH Price: ${snapshot.eth_price_usd:.2f}")
        print(f"  Gas Price: {snapshot.gas_price_gwei:.2f} gwei")
        print(f"  Block Fullness: {snapshot.block_fullness_percent:.1f}%")
        print(f"  Blob Utilization: {snapshot.blob_space_utilization_percent:.1f}%")
        print(f"  Epoch: {snapshot.epoch}")
        print(f"  Data Quality: {snapshot.data_quality.overall_quality_score:.1%}")
        print()
        
        # Test motor command generation
        from cloud.data_aggregator.motor_command_generator import MotorCommandGenerator
        generator = MotorCommandGenerator()
        
        print("Generating motor commands from live data...")
        commands = await generator.generate_commands(snapshot, snapshot.epoch)
        
        print(f"Motor Commands Generated:")
        for motor_name, command in commands.motors.items():
            print(f"  {motor_name}: {command.velocity_rpm:.1f} RPM {command.direction}")
        
        print()
        print("SUCCESS: System is using 100% LIVE blockchain data!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_live_blockchain_fetcher())
    if success:
        print("\nSystem is ready for live blockchain data!")
    else:
        print("\nSystem still has issues with live data.")