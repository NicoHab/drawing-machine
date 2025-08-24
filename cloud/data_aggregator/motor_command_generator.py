"""
Motor Command Generator

Converts blockchain data into motor control commands using algorithmic mapping
between Ethereum metrics and drawing machine motor parameters.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional

from shared.models.blockchain_data import EthereumDataSnapshot, MarketCondition, ActivityLevel
from shared.models.motor_commands import (
    MotorVelocityCommands,
    MotorSafetyLimits,
    MotorDirection,
    MotorName,
    SingleMotorCommand,
)


class GenerationError(Exception):
    """Exception raised when motor command generation fails."""
    
    def __init__(self, message: str, blockchain_data: Optional[EthereumDataSnapshot] = None):
        self.blockchain_data = blockchain_data
        super().__init__(message)


class MotorCommandGenerator:
    """
    Generates motor control commands from blockchain data.
    
    Maps Ethereum blockchain metrics to drawing machine motor parameters
    using configurable algorithms and safety constraints.
    """
    
    def __init__(self, safety_limits: Optional[MotorSafetyLimits] = None):
        self.safety_limits = safety_limits or MotorSafetyLimits()
        self.logger = logging.getLogger(__name__)
        
        # Algorithm configuration
        self.config = {
            # Price-to-canvas mapping
            "canvas_price_sensitivity": 0.01,  # RPM per USD
            "canvas_baseline_rpm": 10.0,
            
            # Gas-to-pen-brush mapping  
            "pen_brush_gas_sensitivity": 0.5,  # RPM per Gwei
            "pen_brush_baseline_rpm": 5.0,
            
            # Network congestion to color depth
            "color_depth_congestion_sensitivity": 0.3,  # RPM per % congestion
            "color_depth_baseline_rpm": 8.0,
            
            # Staking to pen elevation
            "pen_elevation_staking_sensitivity": 0.8,  # RPM per % staked
            "pen_elevation_baseline_rpm": 6.0,
            
            # Utilization-based RPM mapping for blob and block motors
            "utilization_target_percent": 50.0,      # Target utilization (0 RPM point)
            "utilization_max_cw_rpm": 10.0,         # Max RPM at 100% utilization (CW)
            "utilization_max_ccw_rpm": 10.0,        # Max RPM at 0% utilization (CCW)
            "utilization_min_percent": 0.0,         # Minimum utilization
            "utilization_max_percent": 100.0,       # Maximum utilization
            
            # Safety margins
            "safety_margin_percent": 0.1,  # 10% safety margin from max RPM
        }
    
    def _calculate_utilization_based_motor(self, utilization_percent: float) -> tuple[float, MotorDirection]:
        """
        Calculate RPM and direction based on utilization percentage using linear mapping with base RPM.
        
        Enhanced linear mapping with base movement:
        - 0% utilization = (max_ccw_rpm + 1) CCW
        - target_percent (50%) = 1 RPM (base movement)
        - 100% utilization = (max_cw_rpm + 1) CW
        
        Args:
            utilization_percent: Network utilization percentage (0-100)
            
        Returns:
            tuple: (velocity_rpm, direction)
        """
        target = self.config["utilization_target_percent"]
        max_cw_rpm = self.config["utilization_max_cw_rpm"] 
        max_ccw_rpm = self.config["utilization_max_ccw_rpm"]
        base_rpm = 1.0  # Base RPM for continuous movement at target
        
        # Clamp utilization to valid range
        util = max(0.0, min(100.0, utilization_percent))
        
        if util >= target:
            # Above target: 1 RPM at target, (max_cw_rpm + 1) at 100%
            # Linear interpolation: rpm = 1 + (util - target) / (100 - target) * max_cw_rpm
            if target >= 100.0:  # Edge case
                velocity_rpm = base_rpm
            else:
                velocity_rpm = base_rpm + (util - target) / (100.0 - target) * max_cw_rpm
            direction = MotorDirection.CLOCKWISE
        else:
            # Below target: (max_ccw_rpm + 1) at 0%, 1 RPM at target
            # Linear interpolation: rpm = 1 + (target - util) / target * max_ccw_rpm
            if target <= 0.0:  # Edge case
                velocity_rpm = base_rpm
            else:
                velocity_rpm = base_rpm + (target - util) / target * max_ccw_rpm
            direction = MotorDirection.COUNTER_CLOCKWISE
        
        return abs(velocity_rpm), direction
    
    def _calculate_gas_target_based_motor(self, gas_ratio_percent: float) -> tuple[float, MotorDirection]:
        """
        Ultra-sensitive gas target mapping with continuous base movement.
        
        Based on historical analysis of 2023-2024 Ethereum data:
        - 58.7% of time, gas ratios are 98-102% (normal conditions)
        - Traditional wide range (95-105%) resulted in minimal motor activity
        - New sensitive range captures subtle network equilibrium changes
        - Base RPM ensures continuous artistic movement even at perfect equilibrium
        
        Enhanced sensitive mapping:
        - 99.0% gas ratio → base_rpm + max_additional_rpm CCW (network spare capacity)
        - 100.0% gas ratio → base_rpm CW (perfect equilibrium, steady movement)  
        - 101.0% gas ratio → base_rpm + max_additional_rpm CW (network congestion)
        
        Args:
            gas_ratio_percent: Gas price as percentage of base fee (100% = at target)
            
        Returns:
            tuple: (velocity_rpm, direction)
        """
        target = 100.0  # 100% = gas price equals base fee target
        sensitivity_range = 1.0  # ±1% from target = full additional motor range
        max_cw_rpm = self.config["utilization_max_cw_rpm"]
        max_ccw_rpm = self.config["utilization_max_ccw_rpm"]
        
        # Base RPM for continuous movement (1 RPM clockwise at equilibrium)
        base_rpm = 1.0
        max_additional_rpm = max_cw_rpm - base_rpm  # Reserve base_rpm for continuous movement
        
        # Calculate deviation from target
        deviation = gas_ratio_percent - target  # -1 to +1 in typical conditions
        
        # Clamp to sensitivity range for smooth operation
        deviation = max(-sensitivity_range, min(sensitivity_range, deviation))
        
        if deviation >= 0:
            # Above target: network congestion, clockwise rotation
            # Base movement + additional based on congestion level
            additional_rpm = (deviation / sensitivity_range) * max_additional_rpm
            velocity_rpm = base_rpm + additional_rpm
            direction = MotorDirection.CLOCKWISE
        else:
            # Below target: network spare capacity, counter-clockwise rotation
            # Additional movement based on spare capacity level  
            additional_rpm = (abs(deviation) / sensitivity_range) * max_additional_rpm
            velocity_rpm = base_rpm + additional_rpm
            direction = MotorDirection.COUNTER_CLOCKWISE
        
        return velocity_rpm, direction
    
    async def generate_commands(
        self, 
        blockchain_data: EthereumDataSnapshot,
        epoch: int = 0,
        duration: float = 3.4
    ) -> MotorVelocityCommands:
        """
        Generate motor velocity commands from blockchain data.
        
        Args:
            blockchain_data: Current blockchain state
            epoch: Drawing epoch number
            duration: Command duration in seconds
            
        Returns:
            MotorVelocityCommands: Complete motor command set
            
        Raises:
            GenerationError: If command generation fails
        """
        try:
            self.logger.debug(f"Generating motor commands for epoch {epoch}")
            
            # Calculate individual motor commands
            canvas_command = await self._generate_canvas_command(blockchain_data)
            pen_brush_command = await self._generate_pen_brush_command(blockchain_data)
            color_depth_command = await self._generate_color_depth_command(blockchain_data)
            pen_elevation_command = await self._generate_pen_elevation_command(blockchain_data)
            
            # Create motor commands dictionary
            motors = {
                MotorName.CANVAS.value: canvas_command,
                MotorName.PEN_BRUSH.value: pen_brush_command,
                MotorName.PEN_COLOR_DEPTH.value: color_depth_command,
                MotorName.PEN_ELEVATION.value: pen_elevation_command,
            }
            
            # Apply safety limits
            self._apply_safety_limits(motors)
            
            # Create calculation metadata
            metadata = self._create_calculation_metadata(blockchain_data)
            
            # Generate complete command set
            commands = MotorVelocityCommands(
                epoch=epoch,
                command_duration_seconds=duration,
                motors=motors,
                source_data=blockchain_data,
                calculation_metadata=metadata,
                safety_limits=self.safety_limits,
            )
            
            self.logger.info(f"Generated motor commands: Canvas={canvas_command.velocity_rpm:.1f}, "
                           f"PB={pen_brush_command.velocity_rpm:.1f}, "
                           f"PCD={color_depth_command.velocity_rpm:.1f}, "
                           f"PE={pen_elevation_command.velocity_rpm:.1f}")
            
            return commands
            
        except Exception as e:
            self.logger.error(f"Failed to generate motor commands: {e}")
            raise GenerationError(f"Command generation failed: {e}", blockchain_data)
    
    async def _generate_canvas_command(self, data: EthereumDataSnapshot) -> SingleMotorCommand:
        """Generate canvas motor command based on ETH price."""
        # Map ETH price to canvas rotation speed
        # Higher prices = faster canvas rotation
        price_factor = (data.eth_price_usd - 2000) * self.config["canvas_price_sensitivity"]
        base_rpm = self.config["canvas_baseline_rpm"]
        
        velocity_rpm = max(0, base_rpm + price_factor)
        
        # Market condition affects direction
        market_condition = data.get_market_condition()
        direction = MotorDirection.CLOCKWISE if market_condition in [MarketCondition.BULL, MarketCondition.VOLATILE] else MotorDirection.COUNTER_CLOCKWISE
        
        return SingleMotorCommand(
            velocity_rpm=velocity_rpm,
            direction=direction,
        )
    
    async def _generate_pen_brush_command(self, data: EthereumDataSnapshot) -> SingleMotorCommand:
        """Generate pen brush motor command based on blob space utilization."""
        # Swapped from gas-target to blob utilization algorithm with base RPM
        # Use utilization-based RPM calculation with continuous movement
        # 0% = 11 RPM CCW, 50% = 1 RPM (base), 100% = 11 RPM CW
        velocity_rpm, direction = self._calculate_utilization_based_motor(data.blob_space_utilization_percent)
        
        return SingleMotorCommand(
            velocity_rpm=velocity_rpm,
            direction=direction,
        )
    
    async def _generate_color_depth_command(self, data: EthereumDataSnapshot) -> SingleMotorCommand:
        """Generate color depth motor command based on gas price relative to base fee target."""
        # Swapped from blob utilization to gas-target algorithm with base RPM
        # Use gas-target-based RPM calculation with continuous movement  
        # 99% gas ratio = 11 RPM CCW, 100% gas ratio = 1 RPM (base), 101% gas ratio = 11 RPM CW
        
        # Calculate gas price as percentage of base fee (100% = at target)
        if data.base_fee_gwei > 0:
            gas_ratio_percent = (data.gas_price_gwei / data.base_fee_gwei) * 100
        else:
            # Fallback if base fee is 0 (shouldn't happen)
            gas_ratio_percent = 100.0
            
        # Use gas-target-based motor calculation with base RPM for continuous movement
        # Target is 100% (gas price == base fee)
        velocity_rpm, direction = self._calculate_gas_target_based_motor(gas_ratio_percent)
        
        return SingleMotorCommand(
            velocity_rpm=velocity_rpm,
            direction=direction,
        )
    
    async def _generate_pen_elevation_command(self, data: EthereumDataSnapshot) -> SingleMotorCommand:
        """Generate pen elevation motor command based on block fullness."""
        # Use utilization-based RPM calculation
        # 0% = 11 RPM CCW, 50% = 1 RPM (base), 100% = 11 RPM CW
        velocity_rpm, direction = self._calculate_utilization_based_motor(data.block_fullness_percent)
        
        return SingleMotorCommand(
            velocity_rpm=velocity_rpm,
            direction=direction,
        )
    
    def _apply_safety_limits(self, motors: Dict[str, SingleMotorCommand]) -> None:
        """Apply safety limits to all motor commands."""
        for motor_name_str, command in motors.items():
            motor_name = MotorName(motor_name_str)
            max_rpm = self.safety_limits.get_limit_for_motor(motor_name)
            
            # Apply safety margin
            safety_limit = max_rpm * (1.0 - self.config["safety_margin_percent"])
            
            if command.velocity_rpm > safety_limit:
                original_rpm = command.velocity_rpm
                command.velocity_rpm = safety_limit
                
                self.logger.warning(f"Motor {motor_name.value} velocity limited: {original_rpm:.1f} -> {safety_limit:.1f} RPM")
                
                # Safety limiting applied (metadata would be stored separately if needed)
    
    def _create_calculation_metadata(self, data: EthereumDataSnapshot) -> Dict:
        """Create metadata about command calculation process."""
        return {
            "generation_timestamp": datetime.now().timestamp(),
            "algorithm_version": "1.0",
            "data_quality_score": data.data_quality.overall_quality_score,
            "market_condition": data.get_market_condition().value,
            "activity_level": data.get_activity_level().value,
            "price_range": self._classify_price_range(data.eth_price_usd),
            "gas_range": self._classify_gas_range(data.gas_price_gwei),
            "config_used": self.config.copy(),
            "safety_limits_applied": True,
        }
    
    def _classify_price_range(self, price: float) -> str:
        """Classify ETH price into ranges."""
        if price < 1000:
            return "very_low"
        elif price < 2000:
            return "low"
        elif price < 3000:
            return "medium"
        elif price < 4000:
            return "high"
        else:
            return "very_high"
    
    def _classify_gas_range(self, gas_price: float) -> str:
        """Classify gas price into ranges."""
        if gas_price < 10:
            return "very_low"
        elif gas_price < 25:
            return "low"
        elif gas_price < 50:
            return "medium"
        elif gas_price < 100:
            return "high"
        else:
            return "very_high"
    
    def update_config(self, new_config: Dict) -> None:
        """Update algorithm configuration parameters."""
        self.config.update(new_config)
        self.logger.info(f"Updated generator config: {new_config}")
    
    def get_config(self) -> Dict:
        """Get current algorithm configuration."""
        return self.config.copy()
    
    async def generate_test_commands(self, epoch: int = 0) -> MotorVelocityCommands:
        """Generate test motor commands with mock data."""
        # Create mock blockchain data for testing
        from shared.models.blockchain_data import ApiResponseTimes, DataQuality
        
        mock_data = EthereumDataSnapshot(
            timestamp=datetime.now().timestamp(),
            epoch=epoch,
            eth_price_usd=2500.0,
            gas_price_gwei=25.0,
            base_fee_gwei=20.0,  # Gas price is 125% of base fee target
            blob_space_utilization_percent=60.0,
            block_fullness_percent=80.0,
            data_quality=DataQuality(
                price_data_fresh=True,
                gas_data_fresh=True,
                blob_data_fresh=True,
                block_data_fresh=True,
                overall_quality_score=0.9
            ),
            api_response_times=ApiResponseTimes(
                coinbase_ms=150.0,
                ethereum_rpc_ms=200.0,
                beacon_chain_ms=180.0,
            ),
        )
        
        return await self.generate_commands(mock_data, epoch)