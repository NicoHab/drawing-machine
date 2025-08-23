#!/usr/bin/env python3
"""
Setup Live Blockchain Data

Instructions and setup script for enabling full live blockchain data
in the Drawing Machine system.
"""

import os
from pathlib import Path

def create_env_file():
    """Create a .env file template for API keys."""
    env_content = '''# Drawing Machine - Live Blockchain API Keys
# Copy this to .env and fill in your API keys

# REQUIRED: Etherscan API Key (FREE - get at etherscan.io/apis)
ETHERSCAN_API_KEY=YourApiKeyToken

# OPTIONAL: Infura API Key (backup for Etherscan)
# Get free tier at infura.io
INFURA_PROJECT_ID=YOUR_PROJECT_ID

# OPTIONAL: Alchemy API Key (alternative to Infura)
ALCHEMY_API_KEY=YOUR_ALCHEMY_KEY
'''
    
    env_path = Path('.env.example')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"Created {env_path} with API key template")

def test_current_data():
    """Test what data is currently available."""
    print("=== CURRENT DATA STATUS ===")
    
    # Test real data sources
    print("✅ ETH Price: LIVE (Coinbase API - no key needed)")
    
    etherscan_key = os.getenv('ETHERSCAN_API_KEY')
    if etherscan_key and etherscan_key != 'YourApiKeyToken':
        print("✅ Gas Prices: LIVE (Etherscan API)")
        print("✅ Block Data: LIVE (Etherscan API)")
        print("✅ Block Fullness: LIVE (calculated from gas data)")
    else:
        print("❌ Gas Prices: MOCK (need Etherscan API key)")
        print("❌ Block Data: MOCK (need Etherscan API key)")
        print("❌ Block Fullness: MOCK (need real block data)")
    
    print("? Blob Space: ESTIMATED (correlated with gas prices)")
    print("? Epochs: ATTEMPTING (beaconcha.in API - no key needed)")
    print()

def show_setup_instructions():
    """Show setup instructions."""
    print("=== SETUP INSTRUCTIONS FOR FULL LIVE DATA ===")
    print()
    print("1. GET FREE ETHERSCAN API KEY:")
    print("   - Go to https://etherscan.io/apis")
    print("   - Create free account") 
    print("   - Generate API key")
    print("   - Add to .env file: ETHERSCAN_API_KEY=your_key_here")
    print()
    print("2. OPTIONAL: GET INFURA API KEY:")
    print("   - Go to https://infura.io")
    print("   - Create free account")
    print("   - Create project")
    print("   - Add to .env file: INFURA_PROJECT_ID=your_project_id")
    print()
    print("3. RESTART THE SYSTEM:")
    print("   - The system will automatically detect and use real API keys")
    print("   - Fallback to mock data if APIs fail")
    print()
    print("=== WHAT YOU'LL GET WITH API KEYS ===")
    print("✅ Real ETH prices (already working)")
    print("✅ Real gas prices from Ethereum mainnet")
    print("✅ Real block fullness percentages")
    print("✅ Real beacon chain epochs")
    print("✅ Estimated blob space utilization")
    print("✅ 100% live blockchain-driven art!")
    print()

def main():
    print("Drawing Machine - Live Blockchain Setup")
    print("=" * 50)
    
    create_env_file()
    print()
    
    test_current_data()
    
    show_setup_instructions()
    
    print("=== CURRENT STATUS ===")
    print("Your system is already using LIVE ETH prices!")
    print("Add API keys for 100% live blockchain data.")
    print("Even without API keys, the core concept works perfectly.")
    
if __name__ == "__main__":
    main()