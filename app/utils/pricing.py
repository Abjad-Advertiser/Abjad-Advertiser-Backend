"""Utility module for handling ad pricing and revenue calculations."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel


class PricingError(Exception):
    """Base exception for pricing-related errors."""

    pass


class DeviceType(str, Enum):
    """Supported device types for rate calculations."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


class InteractionType(str, Enum):
    """Types of ad interactions that generate revenue."""

    IMPRESSION = "impression"
    CLICK = "click"
    VIEW = "view"


class RegionRates(BaseModel):
    """Model for region-specific pricing rates."""

    description: str
    countries: list[str]
    rates: dict[str, float]
    currency: str


class PricingConfig(BaseModel):
    """Model for the complete pricing configuration."""

    regions: dict[str, RegionRates]
    default_currency: str
    minimum_payout: float
    payment_schedule: str
    rate_multipliers: dict[str, float]
    last_updated: datetime
    version: str


class PricingManager:
    """Manages ad pricing and revenue calculations."""

    def __init__(self, config_path: str | None = None):
        """Initialize the pricing manager.

        Args:
            config_path: Path to the pricing configuration JSON file.
                       If None, uses the default path.
        """
        if config_path is None:
            config_path = str(
                Path(__file__).parent.parent / "core" / "static" / "pricing_rates.json"
            )

        try:
            with open(config_path) as f:
                config_data = json.load(f)
                self.config = PricingConfig(**config_data)
        except FileNotFoundError:
            raise PricingError(f"Pricing configuration file not found: {config_path}")
        except json.JSONDecodeError:
            raise PricingError(f"Invalid JSON in pricing configuration: {config_path}")

        # Create country to region mapping for faster lookups
        self.country_region_map = {}
        for region, data in self.config.regions.items():
            for country in data.countries:
                self.country_region_map[country] = region

    def get_region_for_country(self, country_code: str) -> str:
        """Get the pricing region for a country code.

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            Region identifier (e.g., 'eu', 'na', etc.)
        """
        return self.country_region_map.get(country_code.upper(), "other")

    def get_base_rate(
        self, country_code: str, interaction_type: str | InteractionType
    ) -> float:
        """Get the base rate for an interaction in a specific country.

        Args:
            country_code: ISO 3166-1 alpha-2 country code
            interaction_type: Type of interaction (impression, click, view)

        Returns:
            Base rate for the interaction
        """
        if isinstance(interaction_type, InteractionType):
            interaction_type = interaction_type.value

        region = self.get_region_for_country(country_code)
        region_data = self.config.regions[region]

        try:
            return region_data.rates[interaction_type]
        except KeyError:
            raise PricingError(f"Invalid interaction type: {interaction_type}")

    def get_device_multiplier(self, device_type: str | DeviceType) -> float:
        """Get the rate multiplier for a device type.

        Args:
            device_type: Type of device (mobile, tablet, desktop)

        Returns:
            Rate multiplier for the device type
        """
        if isinstance(device_type, DeviceType):
            device_type = device_type.value

        try:
            return self.config.rate_multipliers[device_type.lower()]
        except KeyError:
            return 1.0  # Default multiplier if device type not found

    def calculate_revenue(
        self,
        country_code: str,
        interaction_type: str | InteractionType,
        device_type: str | DeviceType,
    ) -> dict:
        """Calculate revenue for an ad interaction.

        Args:
            country_code: ISO 3166-1 alpha-2 country code
            interaction_type: Type of interaction (impression, click, view)
            device_type: Type of device (mobile, tablet, desktop)

        Returns:
            Dict containing:
                - base_rate: Base rate for the interaction
                - device_multiplier: Multiplier for the device type
                - final_rate: Final calculated rate
                - currency: Currency for the rate
        """
        try:
            base_rate = self.get_base_rate(country_code, interaction_type)
            device_multiplier = self.get_device_multiplier(device_type)
            final_rate = base_rate * device_multiplier

            region = self.get_region_for_country(country_code)
            currency = self.config.regions[region].currency

            return {
                "base_rate": base_rate,
                "device_multiplier": device_multiplier,
                "final_rate": final_rate,
                "currency": currency,
            }
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error calculating revenue: {str(e)}",
            )

    @property
    def minimum_payout(self) -> float:
        """Get the minimum payout amount."""
        return self.config.minimum_payout

    @property
    def payment_schedule(self) -> str:
        """Get the payment schedule."""
        return self.config.payment_schedule

    @property
    def last_updated(self) -> datetime:
        """Get the last update timestamp of the pricing configuration."""
        return self.config.last_updated
