#!/usr/bin/env python3
"""
Detailed Etherscan API Debug
Debug exactly what the blockchain fetcher is doing with Etherscan
"""

import asyncio
import json
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

async def test_etherscan_detailed():
    """Test the exact Etherscan API calls that the blockchain fetcher makes."""
    print("DETAILED ETHERSCAN API TEST")
    print("=" * 50)
    
    # Import after loading env vars
    from cloud.data_aggregator.blockchain_fetcher import BlockchainDataFetcher
    import aiohttp
    
    fetcher = BlockchainDataFetcher()
    api_key = os.getenv('ETHERSCAN_API_KEY', 'YourApiKeyToken')
    
    print(f"Using API key: {api_key[:10]}...")
    print(f"Etherscan URL: {fetcher.etherscan_url}")
    print()
    
    try:
        print("Step 1: Testing direct _fetch_etherscan_gas_data method...")
        etherscan_result = await fetcher._fetch_etherscan_gas_data()
        print(f"Result: {etherscan_result}")
        print()
        
        print("Step 2: Testing _fetch_ethereum_rpc_data method...")
        ethereum_result = await fetcher._fetch_ethereum_rpc_data()
        print(f"Result: {ethereum_result}")
        print()
        
        print("Step 3: Testing full blockchain fetch...")
        full_result = await fetcher.fetch_current_data()
        print(f"ETH Price: ${full_result.eth_price_usd:.2f}")
        print(f"Gas Price: {full_result.gas_price_gwei:.2f} gwei")
        print(f"Block Fullness: {full_result.block_fullness_percent:.1f}%")
        print(f"Data Sources: {full_result.data_sources}")
        print()
        
    except Exception as e:
        print(f"ERROR in detailed test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_etherscan_detailed())