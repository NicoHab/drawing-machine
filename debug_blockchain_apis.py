#!/usr/bin/env python3
"""
Debug Blockchain API Calls
Test the actual API responses to see why live data isn't working
"""

import asyncio
import json
import os
from datetime import datetime
import aiohttp

async def test_coinbase_api():
    """Test Coinbase API for ETH price"""
    print("Testing Coinbase API...")
    try:
        url = "https://api.coinbase.com/v2/exchange-rates?currency=ETH"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    eth_price = float(data["data"]["rates"]["USD"])
                    print(f"SUCCESS: ETH Price = ${eth_price:.2f}")
                    return eth_price
                else:
                    print(f"ERROR: Status {response.status}")
                    return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

async def test_etherscan_api():
    """Test Etherscan API with your key"""
    print("Testing Etherscan API...")
    
    # Load API key from environment
    api_key = os.getenv('ETHERSCAN_API_KEY', 'YourApiKeyToken')
    print(f"Using API key: {api_key[:10]}...")
    
    try:
        url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"Raw response: {json.dumps(data, indent=2)}")
                    
                    if 'result' in data and 'SafeGasPrice' in data['result']:
                        gas_price = float(data['result']['SafeGasPrice'])
                        print(f"SUCCESS: Gas Price = {gas_price:.1f} gwei")
                        return gas_price
                    else:
                        print(f"ERROR: Unexpected response format")
                        return None
                else:
                    text = await response.text()
                    print(f"ERROR: Status {response.status}, Response: {text}")
                    return None
                    
    except Exception as e:
        print(f"ERROR: {e}")
        return None

async def test_beacon_chain_api():
    """Test Beacon Chain API"""
    print("Testing Beacon Chain API...")
    try:
        url = "https://api.beaconcha.in/api/v1/epoch/latest"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Raw response: {json.dumps(data, indent=2)}")
                    
                    if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                        epoch_data = data['data'][0]
                        epoch = epoch_data.get('epoch', 'N/A')
                        print(f"SUCCESS: Current Epoch = {epoch}")
                        return epoch
                    else:
                        print(f"ERROR: Unexpected response format")
                        return None
                else:
                    text = await response.text()
                    print(f"ERROR: Status {response.status}, Response: {text}")
                    return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

async def main():
    """Test all blockchain APIs"""
    print("BLOCKCHAIN API DEBUG TEST")
    print("=" * 50)
    print(f"Current time: {datetime.now()}")
    print()
    
    # Test all APIs
    eth_price = await test_coinbase_api()
    print()
    
    gas_price = await test_etherscan_api()
    print()
    
    epoch = await test_beacon_chain_api()
    print()
    
    print("SUMMARY:")
    print(f"ETH Price: {'LIVE' if eth_price else 'FAILED'}")
    print(f"Gas Price: {'LIVE' if gas_price else 'FAILED'}")  
    print(f"Epoch: {'LIVE' if epoch else 'FAILED'}")
    
    if eth_price and gas_price and epoch:
        print()
        print("ALL APIs WORKING! System should use 100% live data.")
    else:
        print()
        print("SOME APIs FAILED! System will use fallback/mock data.")

if __name__ == "__main__":
    asyncio.run(main())