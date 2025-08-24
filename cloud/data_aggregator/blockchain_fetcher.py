"""
Blockchain Data Fetcher

Fetches real-time Ethereum blockchain data from multiple sources and provides
structured data for motor command generation.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from aiohttp import ClientSession, ClientError

from shared.models.blockchain_data import (
    EthereumDataSnapshot,
    ApiResponseTimes,
    DataQuality,
    MarketCondition,
    ActivityLevel,
    BlockchainDataValidationError,
)


class FetchError(Exception):
    """Exception raised when blockchain data fetching fails."""
    
    def __init__(self, message: str, source: str, status_code: Optional[int] = None):
        self.source = source
        self.status_code = status_code
        super().__init__(message)


class BlockchainDataFetcher:
    """
    Fetches real-time Ethereum blockchain data from multiple APIs.
    
    Aggregates data from coinbase, ethereum nodes, and beacon chain
    to provide comprehensive blockchain state for motor control.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.coinbase_url = "https://api.coinbase.com/v2/exchange-rates?currency=ETH"
        # Get from environment variable for security
        infura_key = os.getenv("INFURA_PROJECT_ID", "YOUR_PROJECT_ID")
        self.ethereum_rpc_url = f"https://mainnet.infura.io/v3/{infura_key}"
        
        # Alternative free APIs
        self.etherscan_url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={os.getenv('ETHERSCAN_API_KEY', 'YourApiKeyToken')}"
        self.gas_station_url = "https://ethgasstation.info/api/ethgasAPI.json"
        self.beacon_chain_url = "https://api.beaconcha.in/api/v1/epoch/latest"
        
        # Rate limiting
        self._last_fetch_time = {}
        self._min_fetch_interval = 10.0  # Minimum seconds between API calls
        
        # Fallback data for when APIs are unavailable
        self._fallback_data = {
            "eth_price_usd": 2500.0,
            "gas_price_gwei": 25.0,
            "base_fee_gwei": 20.0,  # Typical base fee slightly below gas price
            "beacon_participation_rate": 95.0,
            "eth_staked_percent": 25.0,
        }
    
    async def fetch_current_data(self) -> EthereumDataSnapshot:
        """
        Fetch current Ethereum blockchain data from multiple sources.
        
        Returns:
            EthereumDataSnapshot: Complete blockchain data snapshot
            
        Raises:
            FetchError: If critical data cannot be fetched
        """
        self.logger.info("Fetching current blockchain data...")
        
        # Track API response times
        start_time = datetime.now()
        api_times = {}
        
        # Fetch data from multiple sources concurrently
        try:
            tasks = [
                self._fetch_coinbase_data(),
                self._fetch_ethereum_rpc_data(),
                self._fetch_beacon_chain_data(),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            coinbase_data, ethereum_data, beacon_data = results
            
            # Handle failed API calls by converting exceptions to empty dicts
            if isinstance(coinbase_data, Exception):
                self.logger.warning(f"Coinbase API failed: {coinbase_data}")
                coinbase_data = {"coinbase_available": False, "eth_price_usd": self._fallback_data["eth_price_usd"]}
            
            if isinstance(ethereum_data, Exception):
                self.logger.warning(f"Ethereum RPC failed: {ethereum_data}")
                ethereum_data = {"ethereum_rpc_available": False, "gas_price_gwei": self._fallback_data["gas_price_gwei"]}
            
            if isinstance(beacon_data, Exception):
                self.logger.warning(f"Beacon chain API failed: {beacon_data}")
                beacon_data = {"beacon_chain_available": False, "current_epoch": 1337}
            
            # Calculate API response times
            api_times = ApiResponseTimes(
                coinbase_ms=self._get_response_time(start_time, "coinbase"),
                ethereum_rpc_ms=self._get_response_time(start_time, "ethereum_rpc"),
                beacon_chain_ms=self._get_response_time(start_time, "beacon_chain"),
            )
            
            # Combine data sources
            combined_data = self._combine_data_sources(coinbase_data, ethereum_data, beacon_data)
            
            # Create data snapshot
            snapshot = EthereumDataSnapshot(
                **combined_data,
                api_response_times=api_times,
            )
            
            self.logger.info(f"Successfully fetched blockchain data: ETH=${snapshot.eth_price_usd:.2f}")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to fetch blockchain data: {e}")
            return await self._create_fallback_snapshot()
    
    async def _fetch_coinbase_data(self) -> Dict:
        """Fetch ETH price data from Coinbase API."""
        try:
            async with ClientSession() as session:
                async with session.get(self.coinbase_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        eth_rate = float(data["data"]["rates"]["USD"])
                        
                        return {
                            "eth_price_usd": eth_rate,
                            "coinbase_available": True,
                        }
                    else:
                        raise FetchError(f"Coinbase API returned {response.status}", "coinbase", response.status)
                        
        except (ClientError, asyncio.TimeoutError) as e:
            self.logger.warning(f"Coinbase API error: {e}")
            return {
                "eth_price_usd": self._fallback_data["eth_price_usd"],
                "coinbase_available": False,
            }
    
    async def _fetch_ethereum_rpc_data(self) -> Dict:
        """Fetch gas price and network data from Ethereum RPC."""
        try:
            # Try Etherscan API first (free, no auth needed for basic tier)
            gas_data = await self._fetch_etherscan_gas_data()
            if gas_data:
                return gas_data
            
            # Fallback to Infura RPC (requires API key)
            return await self._fetch_infura_data()
            
        except Exception as e:
            self.logger.warning(f"All Ethereum data sources failed: {e}")
            return {
                "gas_price_gwei": self._fallback_data["gas_price_gwei"],
                "base_fee_gwei": self._fallback_data["base_fee_gwei"],
                "blob_space_utilization_percent": 50.0,
                "block_fullness_percent": 75.0,
                "ethereum_rpc_available": False,
            }
    
    async def _fetch_etherscan_gas_data(self) -> Dict:
        """Fetch real gas data from Etherscan API (free tier)."""
        try:
            from aiohttp import ClientSession
            
            async with ClientSession() as session:
                # Get gas prices
                self.logger.info("Starting Etherscan gas API request...")
                async with session.get(self.etherscan_url, timeout=10) as response:
                    if response.status == 200:
                        self.logger.info("Gas API response received, parsing JSON...")
                        gas_data = await response.json()
                        self.logger.info(f"Gas data type: {type(gas_data)}, keys: {list(gas_data.keys()) if isinstance(gas_data, dict) else 'Not a dict'}")
                        
                        # Get latest block for fullness data
                        block_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag=latest&boolean=true&apikey={os.getenv('ETHERSCAN_API_KEY', 'YourApiKeyToken')}"
                        self.logger.info("Starting Etherscan block API request...")
                        async with session.get(block_url, timeout=10) as block_response:
                            self.logger.info(f"Block API response status: {block_response.status}")
                            if block_response.status == 200:
                                try:
                                    block_data = await block_response.json()
                                    self.logger.info(f"Block data successfully parsed as JSON: type={type(block_data)}")
                                    if isinstance(block_data, dict):
                                        self.logger.info(f"Block data keys: {list(block_data.keys())}")
                                    else:
                                        self.logger.error(f"Block data is not a dict: {repr(block_data)[:200]}")
                                        block_data = {}
                                except Exception as json_error:
                                    self.logger.error(f"Failed to parse block API response as JSON: {json_error}")
                                    block_data = {}
                            else:
                                self.logger.warning(f"Block API returned status {block_response.status}")
                                block_data = {}
                            
                            # Calculate block fullness and extract block number
                            block_fullness = 75.0  # Default fallback
                            block_number = None
                            
                            self.logger.info(f"Block response keys: {list(block_data.keys()) if isinstance(block_data, dict) else 'Not a dict'}")
                            
                            if 'result' in block_data and block_data['result']:
                                result = block_data['result']
                                self.logger.info(f"Block result type: {type(result)}")
                                
                                if isinstance(result, dict):
                                    try:
                                        gas_used_hex = result.get('gasUsed', '0')
                                        gas_limit_hex = result.get('gasLimit', '0')
                                        block_number_hex = result.get('number', '0')
                                        
                                        self.logger.info(f"Raw hex values: gasUsed={gas_used_hex}, gasLimit={gas_limit_hex}, number={block_number_hex}")
                                        
                                        gas_used = int(gas_used_hex, 16)
                                        gas_limit = int(gas_limit_hex, 16)
                                        block_number = int(block_number_hex, 16)
                                        
                                        if gas_limit > 0:
                                            block_fullness = (gas_used / gas_limit) * 100
                                            
                                        self.logger.info(f"SUCCESS: Parsed block data - gas_used={gas_used:,}, gas_limit={gas_limit:,}, block_number={block_number:,}, fullness={block_fullness:.1f}%")
                                        
                                    except (ValueError, KeyError, TypeError) as e:
                                        self.logger.error(f"Error parsing block data: {e}")
                                        self.logger.error(f"Block result content: {result}")
                                        block_fullness = 75.0
                                else:
                                    self.logger.error(f"Block result is not dict: {type(result)} = {repr(result)[:200]}")
                            else:
                                self.logger.error(f"No valid result in block data: {block_data}")
                        
                        # Validate gas_data structure before accessing
                        self.logger.info(f"Gas data structure: {gas_data}")
                        if not isinstance(gas_data, dict) or 'result' not in gas_data:
                            self.logger.error(f"Invalid gas data structure: {gas_data}")
                            return None
                            
                        gas_result = gas_data['result']
                        self.logger.info(f"Gas result type: {type(gas_result)}, content: {gas_result}")
                        
                        if not isinstance(gas_result, dict) or 'SafeGasPrice' not in gas_result:
                            self.logger.error(f"Invalid gas result structure: {gas_result}")
                            return None
                            
                        safe_gas_price = float(gas_result['SafeGasPrice'])
                        self.logger.info(f"Successfully parsed SafeGasPrice: {safe_gas_price}")
                        
                        # Extract base fee (EIP-1559 target gas price)
                        base_fee_gwei = self._fallback_data["gas_price_gwei"]  # Default fallback
                        if 'suggestBaseFee' in gas_result:
                            try:
                                base_fee_gwei = float(gas_result['suggestBaseFee'])
                                self.logger.info(f"Successfully parsed suggestBaseFee: {base_fee_gwei}")
                            except (ValueError, TypeError) as e:
                                self.logger.warning(f"Failed to parse suggestBaseFee, using fallback: {e}")
                        else:
                            self.logger.warning("No suggestBaseFee in gas API response, using SafeGasPrice as fallback")
                            base_fee_gwei = safe_gas_price * 0.9  # Estimate base fee as ~90% of safe price
                        
                        # Extract block number from gas API (it's already included!)
                        if 'LastBlock' in gas_result:
                            block_number = int(gas_result['LastBlock'])
                            self.logger.info(f"Block number extracted from gas API: {block_number}")
                        else:
                            block_number = None
                            self.logger.warning("No LastBlock in gas API response")
                        
                        # Get enhanced blob utilization from gas utilization ratio
                        blob_utilization = self._estimate_blob_utilization_from_gas_ratio(gas_data)
                        self.logger.info(f"Enhanced blob utilization estimate: {blob_utilization}%")
                        
                        # Get better block fullness estimate from gas utilization ratio
                        block_fullness_estimate = self._estimate_block_fullness_from_gas_ratio(gas_data)
                        self.logger.info(f"Block fullness estimate from gas ratio: {block_fullness_estimate}%")
                        
                        # Use the better estimate if we don't have real block data
                        final_block_fullness = block_fullness if block_fullness != 75.0 else block_fullness_estimate
                        
                        return {
                            "gas_price_gwei": safe_gas_price,
                            "base_fee_gwei": base_fee_gwei,
                            "blob_space_utilization_percent": blob_utilization,
                            "block_fullness_percent": final_block_fullness,
                            "block_number": block_number,
                            "ethereum_rpc_available": True,
                        }
        except Exception as e:
            self.logger.error(f"Etherscan API failed: {e}")
            import traceback
            self.logger.error(f"Etherscan traceback: {traceback.format_exc()}")
            return None
    
    async def _fetch_infura_data(self) -> Dict:
        """Fetch data from Infura RPC (requires API key)."""
        try:
            from aiohttp import ClientSession
            
            # RPC call for gas price
            rpc_payload = {
                "jsonrpc": "2.0",
                "method": "eth_gasPrice",
                "params": [],
                "id": 1
            }
            
            async with ClientSession() as session:
                async with session.post(self.ethereum_rpc_url, json=rpc_payload, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        gas_price_wei = int(data['result'], 16)
                        gas_price_gwei = gas_price_wei / 1e9
                        
                        # Get latest block
                        block_payload = {
                            "jsonrpc": "2.0", 
                            "method": "eth_getBlockByNumber",
                            "params": ["latest", True],
                            "id": 2
                        }
                        
                        async with session.post(self.ethereum_rpc_url, json=block_payload, timeout=10) as block_response:
                            block_data = await block_response.json() if block_response.status == 200 else {}
                            
                            # Calculate block fullness
                            block_fullness = 75.0
                            if 'result' in block_data and block_data['result']:
                                gas_used = int(block_data['result']['gasUsed'], 16)
                                gas_limit = int(block_data['result']['gasLimit'], 16)
                                block_fullness = (gas_used / gas_limit) * 100
                        
                        return {
                            "gas_price_gwei": gas_price_gwei,
                            "base_fee_gwei": gas_price_gwei * 0.85,  # Estimate base fee as ~85% of current gas price
                            "blob_space_utilization_percent": self._estimate_blob_utilization_from_block(block_data),
                            "block_fullness_percent": block_fullness,
                            "ethereum_rpc_available": True,
                        }
        except Exception as e:
            self.logger.debug(f"Infura RPC failed: {e}")
            raise e
    
    def _estimate_blob_utilization(self, gas_data) -> float:
        """Estimate blob space utilization from gas data."""
        try:
            # High gas prices often correlate with high blob usage
            if isinstance(gas_data, dict) and 'result' in gas_data:
                result = gas_data['result']
                if isinstance(result, dict) and 'SafeGasPrice' in result:
                    safe_gas = float(result['SafeGasPrice'])
                else:
                    self.logger.warning(f"Gas data result is not dict or missing SafeGasPrice: {result}")
                    safe_gas = 25.0  # Default
            else:
                self.logger.warning(f"Invalid gas data structure in _estimate_blob_utilization: {gas_data}")
                safe_gas = 25.0  # Default
                
            if safe_gas > 40:
                return 80.0
            elif safe_gas > 25:
                return 60.0
            else:
                return 30.0
        except Exception as e:
            self.logger.error(f"Error in _estimate_blob_utilization: {e}")
            return 50.0  # Safe fallback
    
    def _estimate_blob_utilization_from_gas_ratio(self, gas_data) -> float:
        """Enhanced blob utilization estimate using gas utilization ratios."""
        try:
            if isinstance(gas_data, dict) and 'result' in gas_data:
                result = gas_data['result']
                if isinstance(result, dict) and 'gasUsedRatio' in result:
                    # Parse gas utilization ratios (last 5 blocks)
                    gas_ratios = result['gasUsedRatio'].split(',')
                    ratios = [float(r) for r in gas_ratios if r.strip()]
                    
                    if ratios:
                        # Average gas utilization across recent blocks
                        avg_gas_util = sum(ratios) / len(ratios)
                        # Convert to percentage and scale for blob estimate
                        # Higher gas usage often correlates with blob activity
                        blob_estimate = min(95.0, avg_gas_util * 85.0)  # Scale to 0-95%
                        self.logger.debug(f"Gas ratios: {ratios}, avg: {avg_gas_util:.3f}, blob est: {blob_estimate:.1f}%")
                        return blob_estimate
            
            self.logger.debug("No gas utilization ratios available, using fallback")
            return 35.0  # Better default than fixed 30%
        except Exception as e:
            self.logger.error(f"Error estimating blob utilization from gas ratios: {e}")
            return 35.0
    
    def _estimate_block_fullness_from_gas_ratio(self, gas_data) -> float:
        """Enhanced block fullness estimate using gas utilization ratios."""
        try:
            if isinstance(gas_data, dict) and 'result' in gas_data:
                result = gas_data['result']
                if isinstance(result, dict) and 'gasUsedRatio' in result:
                    # Parse gas utilization ratios (last 5 blocks)  
                    gas_ratios = result['gasUsedRatio'].split(',')
                    ratios = [float(r) for r in gas_ratios if r.strip()]
                    
                    if ratios:
                        # Use most recent block's gas utilization as fullness estimate
                        latest_ratio = ratios[-1] if ratios else 0.5
                        block_fullness = latest_ratio * 100  # Convert to percentage
                        self.logger.debug(f"Latest gas ratio: {latest_ratio:.3f}, block fullness: {block_fullness:.1f}%")
                        return min(100.0, block_fullness)
            
            self.logger.debug("No gas utilization ratios available for block fullness")
            return 65.0  # Better default than fixed 75%
        except Exception as e:
            self.logger.error(f"Error estimating block fullness from gas ratios: {e}")
            return 65.0
    
    def _estimate_blob_utilization_from_block(self, block_data) -> float:
        """Estimate blob utilization from block data."""
        try:
            if 'result' in block_data and 'blobGasUsed' in block_data['result']:
                blob_gas_used = int(block_data['result']['blobGasUsed'], 16)
                # Max blob gas per block is roughly 786,432
                max_blob_gas = 786432
                return (blob_gas_used / max_blob_gas) * 100
        except:
            pass
        return 50.0  # Default estimate
    
    async def _fetch_beacon_chain_data(self) -> Dict:
        """Fetch beacon chain data for Ethereum 2.0 metrics."""
        try:
            from aiohttp import ClientSession
            
            async with ClientSession() as session:
                async with session.get(self.beacon_chain_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract real epoch data from beaconcha.in API
                        if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                            epoch_data = data['data'][0]  # Latest epoch
                            current_epoch = epoch_data.get('epoch', 1337)
                            participation = epoch_data.get('attestationspercentage', 95.0)
                            
                            return {
                                "current_epoch": current_epoch,
                                "beacon_participation_rate": participation,
                                "validators_count": epoch_data.get('validatorscount', 800000),
                                "beacon_chain_available": True,
                            }
                        
        except Exception as e:
            self.logger.warning(f"Beacon chain API error: {e}")
            
        # Fallback to calculated epoch based on current time
        # Beacon chain started at slot 0 on Dec 1, 2020, 12:00:23 UTC
        import time
        beacon_genesis = 1606824023  # Dec 1, 2020 12:00:23 UTC
        current_time = int(time.time())
        slots_since_genesis = (current_time - beacon_genesis) // 12  # 12 seconds per slot
        epoch_since_genesis = slots_since_genesis // 32  # 32 slots per epoch
        estimated_epoch = epoch_since_genesis
        
        return {
            "current_epoch": estimated_epoch,  # Calculated realistic epoch
            "beacon_participation_rate": self._fallback_data["beacon_participation_rate"],
            "validators_count": 800000,
            "beacon_chain_available": False,
        }
    
    def _combine_data_sources(self, coinbase_data: Dict, ethereum_data: Dict, beacon_data: Dict) -> Dict:
        """Combine data from multiple sources into a unified structure."""
        
        # Safely extract data with fallbacks
        eth_price = coinbase_data.get("eth_price_usd", self._fallback_data["eth_price_usd"]) if coinbase_data else self._fallback_data["eth_price_usd"]
        gas_price = ethereum_data.get("gas_price_gwei", self._fallback_data["gas_price_gwei"]) if ethereum_data else self._fallback_data["gas_price_gwei"]
        base_fee_gwei = ethereum_data.get("base_fee_gwei", self._fallback_data["base_fee_gwei"]) if ethereum_data else self._fallback_data["base_fee_gwei"]
        blob_util = ethereum_data.get("blob_space_utilization_percent", 50.0) if ethereum_data else 50.0
        block_fullness = ethereum_data.get("block_fullness_percent", 75.0) if ethereum_data else 75.0
        block_number = ethereum_data.get("block_number", None) if ethereum_data else None
        current_epoch = beacon_data.get("current_epoch", 1337) if beacon_data else 1337
        
        # Calculate derived metrics
        market_condition = self._determine_market_condition(eth_price)
        activity_level = self._determine_activity_level(gas_price, blob_util)
        
        data_quality = DataQuality(
            price_data_fresh=coinbase_data.get("coinbase_available", False) if coinbase_data else False,
            gas_data_fresh=ethereum_data.get("ethereum_rpc_available", False) if ethereum_data else False,
            blob_data_fresh=ethereum_data.get("ethereum_rpc_available", False) if ethereum_data else False,
            block_data_fresh=ethereum_data.get("ethereum_rpc_available", False) if ethereum_data else False,
            overall_quality_score=self._calculate_data_quality_score(coinbase_data or {}, ethereum_data or {}, beacon_data or {}) / 100.0
        )
        
        # Determine data sources for logging with enhanced accuracy
        eth_source = "coinbase.com/api" if coinbase_data and coinbase_data.get("coinbase_available") else "fallback"
        gas_source = "etherscan.io/api" if ethereum_data and ethereum_data.get("ethereum_rpc_available") else "fallback"
        epoch_source = "beaconcha.in/api" if beacon_data and beacon_data.get("beacon_chain_available") else "calculated"
        
        # More specific data sources
        block_source = "etherscan.io/gas-api" if ethereum_data and ethereum_data.get("block_number") else "fallback"
        blob_source = "etherscan.io/gas-ratios" if ethereum_data and ethereum_data.get("ethereum_rpc_available") else "estimated"
        fullness_source = "etherscan.io/gas-ratios" if ethereum_data and ethereum_data.get("ethereum_rpc_available") else "fallback"
        
        return {
            "timestamp": datetime.now().timestamp(),
            "epoch": current_epoch,
            "eth_price_usd": eth_price,
            "gas_price_gwei": gas_price,
            "base_fee_gwei": base_fee_gwei,
            "blob_space_utilization_percent": blob_util,
            "block_fullness_percent": block_fullness,
            "block_number": block_number,
            "data_quality": data_quality,
            # Data source tracking for enhanced logging
            "data_sources": {
                "eth_price_source": eth_source,
                "gas_price_source": gas_source,
                "blob_util_source": blob_source,  # From gas utilization ratios
                "block_fullness_source": fullness_source,  # From gas utilization ratios
                "epoch_source": epoch_source,
                "block_number_source": block_source,  # From gas API LastBlock field
            }
        }
    
    def _determine_market_condition(self, eth_price: float) -> MarketCondition:
        """Determine market condition based on ETH price."""
        if eth_price < 1500:
            return MarketCondition.BEAR
        elif eth_price < 2500:
            return MarketCondition.SIDEWAYS
        elif eth_price < 4000:
            return MarketCondition.BULL
        else:
            return MarketCondition.VOLATILE
    
    def _determine_activity_level(self, gas_price: float, blob_utilization: float) -> ActivityLevel:
        """Determine network activity level based on gas price and blob utilization."""
        activity_score = (gas_price / 50.0) + (blob_utilization / 100.0)
        
        if activity_score < 0.5:
            return ActivityLevel.LOW
        elif activity_score < 1.0:
            return ActivityLevel.MODERATE
        elif activity_score < 1.5:
            return ActivityLevel.HIGH
        else:
            return ActivityLevel.EXTREME
    
    def _calculate_data_quality_score(self, coinbase_data: Dict, ethereum_data: Dict, beacon_data: Dict) -> float:
        """Calculate data quality score based on API availability."""
        available_apis = sum([
            coinbase_data.get("coinbase_available", False),
            ethereum_data.get("ethereum_rpc_available", False),
            beacon_data.get("beacon_chain_available", False),
        ])
        
        return (available_apis / 3.0) * 100.0
    
    def _get_response_time(self, start_time: datetime, api_name: str) -> float:
        """Get API response time in milliseconds."""
        # This is a simplified implementation
        # In practice, you'd track individual API call times
        return (datetime.now() - start_time).total_seconds() * 1000 / 3
    
    async def _create_fallback_snapshot(self) -> EthereumDataSnapshot:
        """Create a fallback data snapshot when APIs are unavailable."""
        self.logger.warning("Using fallback blockchain data")
        
        data_quality = DataQuality(
            price_data_fresh=False,
            gas_data_fresh=False,
            blob_data_fresh=False,
            block_data_fresh=False,
            overall_quality_score=0.0  # Indicates fallback data
        )
        
        return EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=1337,  # Valid epoch number
            eth_price_usd=self._fallback_data["eth_price_usd"],
            gas_price_gwei=self._fallback_data["gas_price_gwei"],
            base_fee_gwei=self._fallback_data["base_fee_gwei"],
            blob_space_utilization_percent=50.0,
            block_fullness_percent=75.0,
            data_quality=data_quality,
            api_response_times=ApiResponseTimes(
                coinbase_ms=0.0,
                ethereum_rpc_ms=0.0,
                beacon_chain_ms=0.0,
            ),
        )
    
    async def get_historical_data(self, hours_back: int = 24) -> List[EthereumDataSnapshot]:
        """
        Get historical blockchain data for analysis.
        
        Args:
            hours_back: Number of hours of historical data to fetch
            
        Returns:
            List of historical data snapshots
        """
        # This would fetch real historical data
        # For now, return empty list
        self.logger.info(f"Historical data fetch requested for {hours_back} hours")
        return []
    
    def get_data_sources_status(self) -> Dict[str, bool]:
        """Get current status of all data sources."""
        return {
            "coinbase": True,      # Would check actual API status
            "ethereum_rpc": True,  # Would check actual RPC status  
            "beacon_chain": True,  # Would check actual beacon status
        }
    
    async def get_latest_block_number(self) -> int:
        """Get the latest Ethereum block number."""
        try:
            # Try Etherscan API first
            block_url = f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={os.getenv('ETHERSCAN_API_KEY', 'YourApiKeyToken')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(block_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            block_number = int(data['result'], 16)
                            self.logger.debug(f"Latest block from Etherscan: {block_number}")
                            return block_number
            
            # Fallback: Calculate estimated block number based on time
            # Ethereum averages ~12 seconds per block
            import time
            # Approximate block 1 timestamp: 1438269988 (July 30, 2015)
            genesis_timestamp = 1438269988
            current_timestamp = int(time.time())
            estimated_block = (current_timestamp - genesis_timestamp) // 12
            
            self.logger.warning(f"Using estimated block number: {estimated_block}")
            return estimated_block
            
        except Exception as e:
            self.logger.error(f"Failed to get latest block number: {e}")
            # Return a reasonable fallback
            return 23205000
    
    async def wait_for_new_block(self, last_known_block: int, max_wait_seconds: int = 30) -> int:
        """Wait for a new block to be mined, return the new block number."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                current_block = await self.get_latest_block_number()
                if current_block > last_known_block:
                    self.logger.info(f"New block detected: {current_block} (was {last_known_block})")
                    return current_block
                
                # Wait 3 seconds before checking again
                await asyncio.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Error waiting for new block: {e}")
                await asyncio.sleep(5)
        
        # Timeout reached, return current block anyway
        self.logger.warning(f"Timeout waiting for new block after {max_wait_seconds}s")
        return await self.get_latest_block_number()