from datetime import datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class CampaignCreate(BaseModel):
    name: str
    description: str
    advertisement_id: str

    campaign_start_date: datetime
    campaign_end_date: datetime

    budget_allocation_currency: str
    budget_allocation_amount: Decimal = Field(
        ..., ge=Decimal("0.01"), le=Decimal("49.99"), decimal_places=2
    )

    @field_validator("budget_allocation_currency")
    def validate_currency(cls, v):
        if v not in ["USD", "SAR"]:
            raise ValueError("Currency must be USD or SAR")
        return v

    @field_validator("budget_allocation_amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        elif v >= 50:
            raise ValueError("Amount must be less than 50")
        return v

    @field_validator("campaign_start_date")
    def validate_campaign_start_date(cls, v):
        max_start_date = datetime.now() + timedelta(days=60)
        if v > max_start_date:
            raise ValueError(
                "Campaign start date cannot be more than 2 months from now"
            )
        return v

    @field_validator("campaign_end_date")
    def validate_campaign_duration(cls, v, values):
        start_date = values.data.get("campaign_start_date")
        if start_date and v:
            if v <= start_date:
                raise ValueError("Campaign end date must be after start date")
            min_duration = timedelta(minutes=30)
            if v - start_date < min_duration:
                raise ValueError("Campaign duration cannot be less than 30 minutes")
            max_duration = timedelta(days=30)
            if v - start_date > max_duration:
                raise ValueError("Campaign duration cannot exceed 30 days")
        return v
