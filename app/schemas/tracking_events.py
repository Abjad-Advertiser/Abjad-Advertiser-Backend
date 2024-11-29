from datetime import datetime

from pydantic import BaseModel, Field

from app.models.tracking_events import EventType


class TrackingEventBase(BaseModel):
    campaign_id: str
    event_type: EventType
    viewer_user_agent: str = Field(..., description="Complete user agent string")
    viewer_session_id: str = Field(..., description="Unique session identifier")
    viewer_screen_resolution: str = Field(
        ..., description="Screen resolution in WxH format"
    )
    viewer_language: str = Field(..., description="ISO 639-1 language code with region")


class TrackingEventCreate(TrackingEventBase):
    pass


class TrackingEventResponse(TrackingEventBase):
    id: str
    event_timestamp: datetime
    viewer_country: str
    viewer_device: str
    viewer_os: str
    viewer_browser: str
    viewer_timezone: str
    last_view_timestamp: datetime | None = None

    class Config:
        from_attributes = True
