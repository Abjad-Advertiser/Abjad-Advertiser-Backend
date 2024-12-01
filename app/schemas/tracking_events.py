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


class TrackingEventResponse(BaseModel):
    status: str = "ok"

    class Config:
        from_attributes = True
