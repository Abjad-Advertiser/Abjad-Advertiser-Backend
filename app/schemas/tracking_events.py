from pydantic import BaseModel

from app.models.tracking_events import EventType


class TrackingEvent(BaseModel):
    ad_id: str
    campaign_id: str
    event_type: EventType
    viewer_user_agent: str
    viewer_session_id: str
