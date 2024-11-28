from fastapi import APIRouter, Depends, Request

from app.dependencies.fast_api_users import current_active_user
from app.models.users import User
from app.schemas.tracking_events import TrackingEvent

tracker_router = APIRouter(tags=["Tracker"])


@tracker_router.post("/track/ad/{ad_id}")
async def track(
    ad_id: str,
    raw_request: Request,
    track_request: TrackingEvent,
    user: User = Depends(current_active_user),
):
    # ip = raw_request.client.host
    pass
