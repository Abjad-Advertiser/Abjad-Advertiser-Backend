"""Schemas for campaign tracking session."""

from datetime import datetime

from pydantic import BaseModel, Field


class CampaignTrackingSessionBase(BaseModel):
    viewer_user_agent: str = Field(..., description="Complete user agent string")
    viewer_screen_resolution: str = Field(
        ..., description="Screen resolution in WxH format"
    )
    viewer_language: str = Field(..., description="ISO 639-1 language code with region")


class CampaignTrackingSessionCreate(CampaignTrackingSessionBase):
    pass


class CampaignTrackingSessionResponse(CampaignTrackingSessionBase):
    id: str
    jwt_token: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
