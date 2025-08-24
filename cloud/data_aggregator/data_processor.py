"""
Data Processor

Orchestrates the complete data processing pipeline from blockchain fetching
to motor command generation with caching, validation, and error handling.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .blockchain_fetcher import BlockchainDataFetcher, FetchError
from .motor_command_generator import MotorCommandGenerator, GenerationError
from shared.models.blockchain_data import EthereumDataSnapshot
from shared.models.motor_commands import MotorVelocityCommands, MotorSafetyLimits


class ProcessingError(Exception):
    """Exception raised when data processing fails."""
    
    def __init__(self, message: str, stage: str, underlying_error: Optional[Exception] = None):
        self.stage = stage
        self.underlying_error = underlying_error
        super().__init__(message)


class DataProcessor:
    """
    Orchestrates the complete blockchain-to-motor-commands pipeline.
    
    Combines blockchain data fetching, processing, caching, and motor command
    generation into a unified service with robust error handling.
    """
    
    def __init__(self, safety_limits: Optional[MotorSafetyLimits] = None):
        self.fetcher = BlockchainDataFetcher()
        self.generator = MotorCommandGenerator(safety_limits)
        self.logger = logging.getLogger(__name__)
        
        # Caching and state - Reduced cache duration for live data
        self._data_cache: Dict[str, EthereumDataSnapshot] = {}
        self._command_cache: Dict[str, MotorVelocityCommands] = {}
        self._cache_duration = timedelta(seconds=30)  # Cache for 30 seconds only for live updates
        
        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "cache_hits": 0,
            "last_process_time": None,
            "average_process_time_ms": 0.0,
        }
        
        # Error tracking
        self._recent_errors: List[Dict] = []
        self._max_error_history = 50
    
    async def process_current_data(self, epoch: int = 0, force_refresh: bool = False) -> MotorVelocityCommands:
        """
        Process current blockchain data into motor commands.
        
        Args:
            epoch: Drawing epoch number
            force_refresh: Skip cache and fetch fresh data
            
        Returns:
            MotorVelocityCommands: Generated motor commands
            
        Raises:
            ProcessingError: If processing pipeline fails
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing data for epoch {epoch}")
            self.stats["total_processed"] += 1
            
            # Check cache first (unless forced refresh)
            if not force_refresh:
                cached_commands = self._get_cached_commands(epoch)
                if cached_commands:
                    self.stats["cache_hits"] += 1
                    self.logger.debug(f"Using cached commands for epoch {epoch}")
                    return cached_commands
            
            # Fetch fresh blockchain data
            blockchain_data = await self._fetch_with_retry()
            
            # Use real blockchain epoch if available, otherwise fall back to parameter
            real_epoch = getattr(blockchain_data, 'epoch', epoch)
            
            # Generate motor commands
            commands = await self._generate_with_validation(blockchain_data, real_epoch)
            
            # Cache the results
            self._cache_data(blockchain_data)
            self._cache_commands(commands, epoch)
            
            # Update statistics
            process_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_processing_stats(process_time, True)
            
            self.logger.info(f"Successfully processed epoch {epoch} in {process_time:.1f}ms")
            return commands
            
        except Exception as e:
            process_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_processing_stats(process_time, False)
            self._record_error("process_current_data", str(e), e)
            
            self.logger.error(f"Failed to process epoch {epoch}: {e}")
            raise ProcessingError(f"Data processing failed for epoch {epoch}", "process_current_data", e)
    
    async def process_batch(self, epochs: List[int]) -> List[Tuple[int, Optional[MotorVelocityCommands]]]:
        """
        Process multiple epochs in batch.
        
        Args:
            epochs: List of epoch numbers to process
            
        Returns:
            List of (epoch, commands) pairs, commands may be None if processing failed
        """
        self.logger.info(f"Processing batch of {len(epochs)} epochs")
        
        # Fetch blockchain data once for all epochs
        try:
            blockchain_data = await self._fetch_with_retry()
        except Exception as e:
            self.logger.error(f"Failed to fetch data for batch processing: {e}")
            return [(epoch, None) for epoch in epochs]
        
        # Process each epoch
        results = []
        for epoch in epochs:
            try:
                commands = await self.generator.generate_commands(blockchain_data, epoch)
                self._cache_commands(commands, epoch)
                results.append((epoch, commands))
                self.stats["successful_generations"] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to generate commands for epoch {epoch}: {e}")
                self._record_error("batch_generation", f"Epoch {epoch}: {e}", e)
                results.append((epoch, None))
                self.stats["failed_generations"] += 1
        
        successful = sum(1 for _, commands in results if commands is not None)
        self.logger.info(f"Batch processing complete: {successful}/{len(epochs)} successful")
        
        return results
    
    async def get_historical_analysis(self, hours_back: int = 24) -> Dict:
        """
        Get historical data analysis for trend detection.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            Analysis results including trends and patterns
        """
        try:
            historical_data = await self.fetcher.get_historical_data(hours_back)
            
            if not historical_data:
                return {"error": "No historical data available"}
            
            # Analyze trends
            analysis = {
                "timeframe_hours": hours_back,
                "data_points": len(historical_data),
                "price_trend": self._analyze_price_trend(historical_data),
                "gas_trend": self._analyze_gas_trend(historical_data),
                "activity_pattern": self._analyze_activity_pattern(historical_data),
                "recommendations": self._generate_recommendations(historical_data),
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Historical analysis failed: {e}")
            return {"error": f"Analysis failed: {e}"}
    
    def get_processing_status(self) -> Dict:
        """Get current processing status and statistics."""
        return {
            "status": "healthy" if self._is_system_healthy() else "degraded",
            "statistics": self.stats.copy(),
            "cache_status": {
                "data_cache_size": len(self._data_cache),
                "command_cache_size": len(self._command_cache),
                "cache_duration_minutes": self._cache_duration.total_seconds() / 60,
            },
            "data_sources": self.fetcher.get_data_sources_status(),
            "recent_errors": self._recent_errors[-5:],  # Last 5 errors
            "last_successful_process": self.stats.get("last_process_time"),
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data and commands."""
        self._data_cache.clear()
        self._command_cache.clear()
        self.logger.info("Cleared all caches")
    
    def update_generator_config(self, config: Dict) -> None:
        """Update motor command generator configuration."""
        self.generator.update_config(config)
        self.logger.info(f"Updated generator configuration: {config}")
    
    def get_commands_by_block_range(self, start_block: int, end_block: int) -> Dict[int, MotorVelocityCommands]:
        """Get cached motor commands for a range of blocks (for historical replay)."""
        commands_by_block = {}
        
        for block_num in range(start_block, end_block + 1):
            block_key = f"block_{block_num}"
            if block_key in self._command_cache:
                commands_by_block[block_num] = self._command_cache[block_key]
        
        self.logger.info(f"Retrieved commands for {len(commands_by_block)}/{end_block - start_block + 1} blocks in range {start_block}-{end_block}")
        return commands_by_block
    
    async def _fetch_with_retry(self, max_retries: int = 3) -> EthereumDataSnapshot:
        """Fetch blockchain data with retry logic."""
        for attempt in range(max_retries):
            try:
                data = await self.fetcher.fetch_current_data()
                self.stats["successful_fetches"] += 1
                return data
                
            except FetchError as e:
                self.stats["failed_fetches"] += 1
                self._record_error("fetch_data", f"Attempt {attempt + 1}: {e}", e)
                
                if attempt == max_retries - 1:
                    raise ProcessingError(f"Failed to fetch data after {max_retries} attempts", "fetch_data", e)
                
                # Exponential backoff
                wait_time = 2 ** attempt
                self.logger.warning(f"Fetch attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
    
    async def _generate_with_validation(self, data: EthereumDataSnapshot, epoch: int) -> MotorVelocityCommands:
        """Generate motor commands with validation."""
        try:
            commands = await self.generator.generate_commands(data, epoch)
            
            # Validate generated commands
            if not self._validate_commands(commands):
                raise ProcessingError("Generated commands failed validation", "validation")
            
            self.stats["successful_generations"] += 1
            return commands
            
        except GenerationError as e:
            self.stats["failed_generations"] += 1
            self._record_error("generate_commands", str(e), e)
            raise ProcessingError(f"Command generation failed: {e}", "generation", e)
    
    def _validate_commands(self, commands: MotorVelocityCommands) -> bool:
        """Validate generated motor commands."""
        try:
            from shared.models.motor_commands import MotorName
            
            # Check that all required motors are present
            required_motors = {motor.value for motor in MotorName}
            provided_motors = set(commands.motors.keys())
            
            if not required_motors.issubset(provided_motors):
                missing = required_motors - provided_motors
                self.logger.error(f"Missing required motors: {missing}")
                return False
            
            # Check that velocities are within reasonable bounds
            for motor_name, command in commands.motors.items():
                if abs(command.velocity_rpm) > 200:  # Reasonable max velocity
                    self.logger.error(f"Excessive velocity for {motor_name}: {command.velocity_rpm}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Command validation failed: {e}")
            return False
    
    def _get_cached_commands(self, epoch: int) -> Optional[MotorVelocityCommands]:
        """Get cached commands if still valid (now using block numbers)."""
        # Try both epoch and block-based cache keys for backward compatibility
        epoch_key = f"epoch_{epoch}"
        block_key = f"block_{epoch}"  # When epoch is actually a block number
        
        # Check block-based cache first (preferred)
        if block_key in self._command_cache:
            return self._command_cache[block_key]
            
        # Fallback to epoch-based cache
        if epoch_key in self._command_cache:
            return self._command_cache[epoch_key]
        
        return None
    
    def _cache_data(self, data: EthereumDataSnapshot) -> None:
        """Cache blockchain data."""
        cache_key = f"data_{int(data.timestamp)}"
        self._data_cache[cache_key] = data
        
        # Clean old cache entries
        self._cleanup_cache()
    
    def _cache_commands(self, commands: MotorVelocityCommands, epoch: int) -> None:
        """Cache generated commands using block-based indexing."""
        # Use block-based cache key for new system
        block_key = f"block_{epoch}"
        self._command_cache[block_key] = commands
        
        # Also cache with epoch key for backward compatibility
        epoch_key = f"epoch_{epoch}"
        self._command_cache[epoch_key] = commands
        
        # Clean old cache entries
        self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Remove old cache entries."""
        current_time = datetime.now()
        cutoff_time = current_time - self._cache_duration
        
        # Cleanup data cache
        keys_to_remove = []
        for key, data in self._data_cache.items():
            data_time = datetime.fromtimestamp(data.timestamp)
            if data_time < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._data_cache[key]
    
    def _update_processing_stats(self, process_time_ms: float, success: bool) -> None:
        """Update processing statistics."""
        self.stats["last_process_time"] = datetime.now().isoformat()
        
        # Update average processing time
        current_avg = self.stats["average_process_time_ms"]
        total_processed = self.stats["total_processed"]
        
        new_avg = ((current_avg * (total_processed - 1)) + process_time_ms) / total_processed
        self.stats["average_process_time_ms"] = new_avg
    
    def _record_error(self, stage: str, message: str, exception: Optional[Exception] = None) -> None:
        """Record error for analysis."""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "message": message,
            "exception_type": type(exception).__name__ if exception else None,
        }
        
        self._recent_errors.append(error_record)
        
        # Keep only recent errors
        if len(self._recent_errors) > self._max_error_history:
            self._recent_errors = self._recent_errors[-self._max_error_history:]
    
    def _is_system_healthy(self) -> bool:
        """Check if the processing system is healthy."""
        # System is healthy if:
        # 1. Recent success rate > 80%
        # 2. No critical errors in last 5 minutes
        # 3. Average processing time < 5 seconds
        
        total = self.stats["total_processed"]
        if total == 0:
            return True
        
        success_rate = (self.stats["successful_fetches"] + self.stats["successful_generations"]) / (total * 2)
        
        return (success_rate > 0.8 and 
                self.stats["average_process_time_ms"] < 5000)
    
    def _analyze_price_trend(self, data: List[EthereumDataSnapshot]) -> str:
        """Analyze ETH price trend from historical data."""
        if len(data) < 2:
            return "insufficient_data"
        
        prices = [d.eth_price_usd for d in data]
        recent_avg = sum(prices[-6:]) / min(6, len(prices))
        older_avg = sum(prices[:6]) / min(6, len(prices))
        
        if recent_avg > older_avg * 1.05:
            return "upward"
        elif recent_avg < older_avg * 0.95:
            return "downward"
        else:
            return "stable"
    
    def _analyze_gas_trend(self, data: List[EthereumDataSnapshot]) -> str:
        """Analyze gas price trend from historical data."""
        if len(data) < 2:
            return "insufficient_data"
        
        gas_prices = [d.gas_price_gwei for d in data]
        recent_avg = sum(gas_prices[-6:]) / min(6, len(gas_prices))
        older_avg = sum(gas_prices[:6]) / min(6, len(gas_prices))
        
        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_activity_pattern(self, data: List[EthereumDataSnapshot]) -> str:
        """Analyze network activity patterns."""
        if len(data) < 2:
            return "insufficient_data"
        
        activity_scores = [d.network_congestion_percent for d in data]
        avg_activity = sum(activity_scores) / len(activity_scores)
        
        if avg_activity > 75:
            return "high_activity"
        elif avg_activity < 25:
            return "low_activity"
        else:
            return "moderate_activity"
    
    def _generate_recommendations(self, data: List[EthereumDataSnapshot]) -> List[str]:
        """Generate recommendations based on historical analysis."""
        recommendations = []
        
        if not data:
            return ["insufficient_data_for_recommendations"]
        
        latest = data[-1]
        
        if latest.data_quality_score < 50:
            recommendations.append("improve_data_source_reliability")
        
        if latest.gas_price_gwei > 50:
            recommendations.append("consider_reducing_pen_brush_sensitivity")
        
        if latest.network_congestion_percent > 80:
            recommendations.append("increase_color_depth_responsiveness")
        
        return recommendations if recommendations else ["no_specific_recommendations"]