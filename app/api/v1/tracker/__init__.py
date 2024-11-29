"""Campaign tracking endpoints with JWT-based session management."""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from ua_parser import parse as parse_ua
from user_agents import parse as parse_user_agent

from app.core.config import settings
from app.db import get_async_session
from app.db.tx_session import TxAsyncSession, get_tx_session
from app.models.campaign_tracking_session import CampaignTrackingSession
from app.models.publisher import Publisher
from app.models.tracking_events import TrackingEvent
from app.schemas.campaign_tracking_session import (
    CampaignTrackingSessionCreate, CampaignTrackingSessionResponse)
from app.schemas.tracking_events import (TrackingEventCreate,
                                         TrackingEventResponse)
from app.services.revenue import RevenueService
from app.utils.device_ua import get_device_type
from app.utils.ip_info_grabber import IPInfoGrabber
from app.utils.sys_logger import LogCategory, Logger, LogLevel

tracker_router = APIRouter(prefix="/track", tags=["Tracker"])

# Constants
JWT_ALGORITHM = "HS256"
RATE_LIMIT_MINUTES = 30
TRACKING_SESSION_COOKIE = "ats_v1"  # Abjad tracking session Version 1
TRACKING_SESSION_EXPIRY = timedelta(hours=1)


def create_tracking_jwt(data: dict) -> str:
    """Create a JWT token for campaign tracking."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + TRACKING_SESSION_EXPIRY
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET, algorithm=JWT_ALGORITHM)


def decode_tracking_jwt(token: str) -> dict:
    """Decode and validate a tracking JWT."""
    try:
        return jwt.decode(token, settings.SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Tracking session has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid tracking session")


async def get_tracking_session(
    request: Request, session: AsyncSession = Depends(get_async_session)
) -> CampaignTrackingSession:
    """Get and validate the tracking session from cookies."""
    jwt_token = request.cookies.get(TRACKING_SESSION_COOKIE)
    if not jwt_token:
        raise HTTPException(
            status_code=401, detail="Missing or invalid tracking session"
        )

    decode_tracking_jwt(jwt_token)

    # Get and validate session
    tracking_session = await CampaignTrackingSession.get_valid_session(
        session, jwt_token, request.client.host, request.headers.get("User-Agent")
    )

    if not tracking_session:
        raise HTTPException(
            status_code=401, detail="Invalid or expired tracking session"
        )

    return tracking_session


@tracker_router.post(
    "/init/{publisher_id}",
    response_model=CampaignTrackingSessionResponse,
    status_code=201,
)
async def init_tracking_session(
    request: Request,
    response: Response,
    publisher_id: str,
    track_request: CampaignTrackingSessionCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Initialize a new campaign tracking session."""
    # TODO: Initlize based on publisher publishing platform
    # ! for now assume and only allow web just to finish
    client_ip = request.client.host
    if not client_ip:
        raise HTTPException(status_code=400, detail="Missing IP address")

    user_agent = track_request.viewer_user_agent
    if not user_agent:
        user_agent = request.headers.get("User-Agent")
        if not user_agent:
            raise HTTPException(status_code=400, detail="Missing user agent")

    # Parse user agent to detect bots
    parsed_user_agent = parse_user_agent(user_agent)
    if parsed_user_agent.is_bot or parsed_user_agent.is_email_client:
        raise HTTPException(status_code=403, detail="Bot traffic not allowed")

    # Create JWT with session data
    jwt_data = {
        "ip": client_ip,
        "ua": user_agent,
        "res": track_request.viewer_screen_resolution,
        "lang": track_request.viewer_language,
    }
    jwt_token = create_tracking_jwt(jwt_data)

    # Create and store session
    tracking_session = await CampaignTrackingSession.create_session(
        session, jwt_token, client_ip, user_agent
    )

    # Set cookie with JWT token
    response.set_cookie(
        key=TRACKING_SESSION_COOKIE,
        value=jwt_token,
        max_age=int(TRACKING_SESSION_EXPIRY.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=True if settings.DEBUG is False else None,  # Only send cookie over HTTPS
        domain=None,  # Allow the cookie to work across subdomains
    )

    return tracking_session


@tracker_router.post(
    "/{campaign_id}/{publisher_id}",
    response_model=TrackingEventResponse,
)
async def track_campaign(
    campaign_id: str,
    publisher_id: str,
    track_request: TrackingEventCreate,
    tracking_session: CampaignTrackingSession = Depends(get_tracking_session),
    session: TxAsyncSession = Depends(get_tx_session()),
):
    """Track campaign views with JWT-based session validation and rate limiting."""
    try:
        client_ip = tracking_session.viewer_ip

        # Check rate limit
        if await CampaignTrackingSession.check_rate_limit(
            session, client_ip, campaign_id
        ):
            raise HTTPException(
                status_code=429,
                detail=f"Already viewed this campaign within the last {RATE_LIMIT_MINUTES} minutes",
            )

        # Get IP info for geolocation
        ip_info_grabber = IPInfoGrabber()
        ip_info = ip_info_grabber.get_ip_info(client_ip)

        # Get publisher
        publisher = await Publisher.get(session, publisher_id)
        if not publisher:
            raise HTTPException(status_code=404, detail="Publisher not found")

        # Parse user agent
        ua = parse_ua(tracking_session.viewer_user_agent)
        device = getattr(ua.device, "brand", "Unknown")
        os = getattr(ua.os, "family", "Unknown")
        browser = getattr(ua.user_agent, "family", "Unknown")

        # Create tracking event
        tracking_event = await TrackingEvent.create_view_event(
            session=session,
            campaign_id=campaign_id,
            ip_info=ip_info,
            device=device,
            device_type=get_device_type(tracking_session.viewer_user_agent),
            os=os,
            browser=browser,
            tracking_session_id=tracking_session.id,
            user_agent=tracking_session.viewer_user_agent,
            publisher_id=publisher_id,
        )

        # Process revenue for the event
        revenue_service = RevenueService()
        revenue_details = await revenue_service.process_tracking_event(
            session, tracking_event, publisher
        )

        # Store this data in a system log
        log = Logger(session)
        await log.log(
            LogLevel.INFO,
            LogCategory.TRACKING,
            f"Processed tracking event for campaign {campaign_id} with revenue details: {revenue_details}",
            event_metadata={
                "tracking_event_id": tracking_event.id,
                "campaign_id": campaign_id,
                "publisher_id": publisher_id,
                "event_type": track_request.event_type,
                "revenue_details": revenue_details,
                "timestamp": datetime.now(UTC),
            },
        )

        # Include revenue details in response
        response_data = TrackingEventResponse(
            id=tracking_event.id,
            campaign_id=campaign_id,
            publisher_id=publisher_id,
            event_type=track_request.event_type,
            revenue_details=revenue_details,
        )

        # Cleanup old blacklisted sessions
        await CampaignTrackingSession.cleanup_blacklist(session)

        return response_data

    except Exception as e:
        # Log any errors
        log = Logger(session)
        await log.log(
            LogLevel.ERROR,
            LogCategory.TRACKING,
            "Failed to process tracking event",
            error=e,
            event_metadata={
                "campaign_id": campaign_id,
                "publisher_id": publisher_id,
                "event_type": track_request.event_type,
            },
        )
