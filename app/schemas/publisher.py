"""Publisher schemas for request/response validation."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PublishingPlatform(str, Enum):
    """Supported publishing platforms."""

    WEBSITE = "website"
    EMAIL = "email"
    MOBILE_APP = "mobile_app"


class PublisherBase(BaseModel):
    """Base publisher attributes."""

    publishing_platform: PublishingPlatform = Field(
        description="Platform where publisher will show ads"
    )


class PublisherCreate(PublisherBase):
    """Schema for creating a new publisher."""

    pass


class PublisherUpdate(BaseModel):
    """Schema for updating a publisher."""

    publishing_platform: PublishingPlatform | None = Field(
        None, description="Platform where publisher will show ads"
    )


class PublisherResponse(PublisherBase):
    """Schema for publisher responses."""

    id: str = Field(description="Unique identifier for the publisher")

    class Config:
        """Pydantic config."""

        from_attributes = True


class DailyRevenue(BaseModel):
    """Daily revenue entry."""

    date: str = Field(description="Date in YYYY-MM-DD format")
    revenue: float = Field(description="Revenue for the day")


class RevenueStats(BaseModel):
    """Schema for publisher revenue statistics."""

    publisher_id: str = Field(description="Publisher ID")
    total_revenue: float = Field(description="Total revenue earned")
    publisher_share: float = Field(description="Publisher's share of revenue")
    platform_share: float = Field(description="Platform's share of revenue")

    interaction_totals: dict[str, int] = Field(
        description="Total counts for views, clicks, and impressions"
    )

    revenue_by_interaction: dict[str, float] = Field(
        description="Revenue breakdown by interaction type (impression, click, view)"
    )
    revenue_by_country: dict[str, float] = Field(
        description="Revenue breakdown by country"
    )
    revenue_by_device: dict[str, float] = Field(
        description="Revenue breakdown by device type"
    )

    daily_revenue_trend: list[DailyRevenue] = Field(
        description="Daily revenue trend for the past 30 days"
    )

    minimum_payout: float = Field(description="Minimum amount required for payout")
    payment_schedule: str = Field(
        description="Payment schedule (e.g., monthly, weekly)"
    )

    stats_period: dict[str, str | None] = Field(
        description="Start and end dates for the statistics period"
    )


class PublisherStats(BaseModel):
    """Schema for publisher statistics."""

    total_revenue: float = Field(description="Total revenue earned")
    total_impressions: int = Field(description="Total number of ad impressions")
    total_clicks: int = Field(description="Total number of ad clicks")
    total_views: int = Field(description="Total number of ad views")
    average_ctr: float = Field(description="Average click-through rate")
    revenue_by_platform: dict = Field(description="Revenue breakdown by platform type")
    revenue_by_country: dict = Field(description="Revenue breakdown by country")


class InteractionRevenue(BaseModel):
    """Revenue details for a specific interaction."""

    count: int = Field(description="Number of interactions")
    revenue: float = Field(description="Revenue from this interaction type")
    share: float = Field(description="Publisher's share for this interaction")


class PeriodicRevenue(BaseModel):
    """Schema for periodic (daily/weekly) revenue breakdown."""

    period_start: datetime = Field(description="Start of the period")
    period_end: datetime = Field(description="End of the period")
    total_revenue: float = Field(description="Total revenue for the period")
    publisher_share: float = Field(description="Publisher's share of revenue")

    impressions: InteractionRevenue = Field(description="Impression statistics")
    clicks: InteractionRevenue = Field(description="Click statistics")
    views: InteractionRevenue = Field(description="View statistics")

    revenue_by_country: dict[str, float] = Field(
        description="Revenue breakdown by country"
    )
    revenue_by_device: dict[str, float] = Field(
        description="Revenue breakdown by device"
    )
