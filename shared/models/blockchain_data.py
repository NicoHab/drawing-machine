"""
Pydantic models for Ethereum blockchain data in the Drawing Machine architecture.

This module provides structured data models for capturing and validating Ethereum
blockchain metrics that drive the drawing machine motors. Each data point corresponds
to specific motor control parameters in the drawing system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator, computed_field


class BlockchainDataValidationError(Exception):
    """Custom exception for blockchain data validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Union[str, int, float]] = None,
    ):
        self.field = field
        self.value = value
        super().__init__(message)


class MarketCondition(str, Enum):
    """Enumeration of market conditions based on ETH price and activity."""

    BEAR = "bear"
    SIDEWAYS = "sideways"
    BULL = "bull"
    VOLATILE = "volatile"


class ActivityLevel(str, Enum):
    """Enumeration of network activity levels."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class ApiResponseTimes(BaseModel):
    """
    API response time measurements for external services.

    Used for monitoring data quality and system health. All times in milliseconds.
    """

    coinbase_ms: float = Field(
        ...,
        ge=0,
        le=30000,
        description="Coinbase API response time in milliseconds (0-30000)",
    )

    ethereum_rpc_ms: float = Field(
        ...,
        ge=0,
        le=30000,
        description="Ethereum RPC API response time in milliseconds (0-30000)",
    )

    beacon_chain_ms: float = Field(
        ...,
        ge=0,
        le=30000,
        description="Beacon Chain API response time in milliseconds (0-30000)",
    )

    @computed_field
    def average_response_time(self) -> float:
        """Calculate average response time across all APIs."""
        return (self.coinbase_ms + self.ethereum_rpc_ms + self.beacon_chain_ms) / 3

    @computed_field
    def is_healthy(self) -> bool:
        """Check if all API response times are within healthy thresholds (< 5000ms)."""
        return all(
            time < 5000
            for time in [self.coinbase_ms, self.ethereum_rpc_ms, self.beacon_chain_ms]
        )

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data

        computed_fields = {"average_response_time", "is_healthy"}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"average_response_time", "is_healthy"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class DataQuality(BaseModel):
    """
    Data quality metrics and freshness indicators.

    Tracks the reliability and timeliness of blockchain data sources.
    """

    price_data_fresh: bool = Field(
        ..., description="Whether ETH price data is fresh (< 60 seconds old)"
    )

    gas_data_fresh: bool = Field(
        ..., description="Whether gas price data is fresh (< 30 seconds old)"
    )

    blob_data_fresh: bool = Field(
        ..., description="Whether blob space data is fresh (< 30 seconds old)"
    )

    block_data_fresh: bool = Field(
        ..., description="Whether block data is fresh (< 15 seconds old)"
    )

    overall_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall data quality score from 0.0 to 1.0"
    )

    @computed_field
    def freshness_score(self) -> float:
        """Calculate freshness score based on boolean freshness flags."""
        fresh_count = sum(
            [
                self.price_data_fresh,
                self.gas_data_fresh,
                self.blob_data_fresh,
                self.block_data_fresh,
            ]
        )
        return fresh_count / 4.0

    @computed_field
    def is_acceptable_quality(self) -> bool:
        """Check if overall data quality meets minimum threshold (> 0.7)."""
        return self.overall_quality_score > 0.7

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data

        computed_fields = {"freshness_score", "is_acceptable_quality"}
        filtered_data = {k: v for k, v in data.items() if k not in computed_fields}
        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {"freshness_score", "is_acceptable_quality"}
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


class EthereumDataSnapshot(BaseModel):
    """
    Complete Ethereum blockchain data snapshot for drawing machine control.

    This model captures all necessary blockchain metrics that drive the four motors
    in the drawing machine system. Each field corresponds to specific motor control
    parameters defined in the Drawing Machine architecture.
    """

    timestamp: float = Field(..., description="Unix timestamp when data was captured")

    epoch: int = Field(
        ...,
        ge=0,
        le=1574,
        description="Drawing epoch number (0-1574), determines drawing session phase",
    )

    eth_price_usd: float = Field(
        ...,
        ge=100,
        le=50000,
        description="ETH price in USD (100-50000), drives canvas motor speed and direction",
    )

    gas_price_gwei: float = Field(
        ...,
        ge=0.1,
        le=1000,
        description="Gas price in Gwei (0.1-1000), drives motor_pb (pen brush) pressure",
    )

    blob_space_utilization_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Blob space utilization percentage (0-100), drives motor_pcd (pen color depth)",
    )

    block_fullness_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Block fullness percentage (0-100), drives motor_pe (pen elevation)",
    )

    data_quality: DataQuality = Field(
        ..., description="Data quality metrics and freshness indicators"
    )

    api_response_times: ApiResponseTimes = Field(
        ..., description="API response time measurements"
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: float) -> float:
        """Validate timestamp is reasonable (not too far in past/future)."""
        now = datetime.now().timestamp()
        if v < now - 86400:  # More than 24 hours ago
            raise BlockchainDataValidationError(
                "Timestamp is too far in the past", field="timestamp", value=v
            )
        if v > now + 3600:  # More than 1 hour in future
            raise BlockchainDataValidationError(
                "Timestamp is too far in the future", field="timestamp", value=v
            )
        return v

    @computed_field
    def datetime_iso(self) -> str:
        """Convert timestamp to ISO format datetime string."""
        return datetime.fromtimestamp(self.timestamp).isoformat()

    @computed_field
    def is_high_activity_epoch(self) -> bool:
        """
        Determine if current epoch represents high network activity.

        High activity is defined as:
        - Gas price > 50 Gwei
        - Block fullness > 80%
        - Blob space utilization > 60%
        """
        return (
            self.gas_price_gwei > 50
            and self.block_fullness_percent > 80
            and self.blob_space_utilization_percent > 60
        )

    def get_market_condition(self) -> MarketCondition:
        """
        Analyze market condition based on ETH price and network activity.

        Returns:
            MarketCondition: Current market state classification
        """
        # Price-based conditions
        if self.eth_price_usd < 2000:
            price_condition = MarketCondition.BEAR
        elif self.eth_price_usd > 4000:
            price_condition = MarketCondition.BULL
        else:
            price_condition = MarketCondition.SIDEWAYS

        # Activity-based volatility check
        is_volatile = (
            self.gas_price_gwei > 100
            or self.block_fullness_percent > 95
            or self.blob_space_utilization_percent > 90
        )

        if is_volatile:
            return MarketCondition.VOLATILE

        return price_condition

    def get_activity_level(self) -> ActivityLevel:
        """
        Determine network activity level based on gas and block metrics.

        Returns:
            ActivityLevel: Current network activity classification
        """
        activity_score = (
            (self.gas_price_gwei / 1000) * 0.4
            + (self.block_fullness_percent / 100) * 0.35
            + (self.blob_space_utilization_percent / 100) * 0.25
        )

        if activity_score < 0.25:
            return ActivityLevel.LOW
        elif activity_score < 0.6:
            return ActivityLevel.MODERATE
        elif activity_score < 0.85:
            return ActivityLevel.HIGH
        else:
            return ActivityLevel.EXTREME

    def get_motor_control_values(self) -> Dict[str, float]:
        """
        Generate normalized motor control values (0.0-1.0) from blockchain data.

        Returns:
            Dict mapping motor names to normalized control values:
            - canvas_motor: ETH price normalized to 0-1 range
            - motor_pb: Gas price normalized to 0-1 range
            - motor_pcd: Blob utilization as percentage (already 0-1)
            - motor_pe: Block fullness as percentage (already 0-1)
        """
        return {
            "canvas_motor": (self.eth_price_usd - 100) / (50000 - 100),
            "motor_pb": (self.gas_price_gwei - 0.1) / (1000 - 0.1),
            "motor_pcd": self.blob_space_utilization_percent / 100,
            "motor_pe": self.block_fullness_percent / 100,
        }

    def is_valid_for_drawing(self) -> bool:
        """
        Check if data quality is sufficient for drawing operations.

        Returns:
            bool: True if data meets quality thresholds for motor control
        """
        return (
            self.data_quality.is_acceptable_quality()
            and self.data_quality.freshness_score() >= 0.75
            and self.api_response_times.is_healthy()
        )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "ignored_types": (property,),
    }

    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that recursively excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json

            data = std_json.loads(json_data)
        else:
            data = json_data.copy() if isinstance(json_data, dict) else json_data

        # Remove root level computed fields
        root_computed_fields = {"datetime_iso", "is_high_activity_epoch"}
        filtered_data = {k: v for k, v in data.items() if k not in root_computed_fields}

        # Filter nested data_quality computed fields
        if "data_quality" in filtered_data and isinstance(
            filtered_data["data_quality"], dict
        ):
            quality_computed = {"freshness_score", "is_acceptable_quality"}
            filtered_data["data_quality"] = {
                k: v
                for k, v in filtered_data["data_quality"].items()
                if k not in quality_computed
            }

        # Filter nested api_response_times computed fields
        if "api_response_times" in filtered_data and isinstance(
            filtered_data["api_response_times"], dict
        ):
            api_computed = {"average_response_time", "is_healthy"}
            filtered_data["api_response_times"] = {
                k: v
                for k, v in filtered_data["api_response_times"].items()
                if k not in api_computed
            }

        return cls.model_validate(filtered_data)

    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {
            "datetime_iso",
            "is_high_activity_epoch",
            "average_response_time",
            "is_healthy",
            "freshness_score",
            "is_acceptable_quality",
        }
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)


# Example schema instances for documentation
EXAMPLE_SCHEMA = {
    "timestamp": 1692123456.789,
    "epoch": 1337,
    "eth_price_usd": 2500.50,
    "gas_price_gwei": 25.5,
    "blob_space_utilization_percent": 75.2,
    "block_fullness_percent": 85.7,
    "data_quality": {
        "price_data_fresh": True,
        "gas_data_fresh": True,
        "blob_data_fresh": True,
        "block_data_fresh": False,
        "overall_quality_score": 0.85,
    },
    "api_response_times": {
        "coinbase_ms": 150.5,
        "ethereum_rpc_ms": 220.1,
        "beacon_chain_ms": 180.3,
    },
}

HIGH_ACTIVITY_EXAMPLE = {
    "timestamp": 1692123456.789,
    "epoch": 800,
    "eth_price_usd": 4200.00,
    "gas_price_gwei": 150.0,
    "blob_space_utilization_percent": 95.0,
    "block_fullness_percent": 98.5,
    "data_quality": {
        "price_data_fresh": True,
        "gas_data_fresh": True,
        "blob_data_fresh": True,
        "block_data_fresh": True,
        "overall_quality_score": 0.95,
    },
    "api_response_times": {
        "coinbase_ms": 100.0,
        "ethereum_rpc_ms": 120.0,
        "beacon_chain_ms": 110.0,
    },
}
