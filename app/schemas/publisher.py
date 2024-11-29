"""Publisher schemas for request/response validation."""

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
    revenue: float = Field(description="Total revenue earned by the publisher")

    class Config:
        """Pydantic config."""

        from_attributes = True


class PublisherStats(BaseModel):
    """Schema for publisher statistics."""

    total_revenue: float = Field(description="Total revenue earned")
    total_impressions: int = Field(description="Total number of ad impressions")
    total_clicks: int = Field(description="Total number of ad clicks")
    total_views: int = Field(description="Total number of ad views")
    average_ctr: float = Field(description="Average click-through rate")
    revenue_by_platform: dict = Field(description="Revenue breakdown by platform type")
    revenue_by_country: dict = Field(description="Revenue breakdown by country")
