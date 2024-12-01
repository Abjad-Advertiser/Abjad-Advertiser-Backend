"""Campaign tracking endpoints with JWT-based session management."""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ua_parser import parse as parse_ua
from user_agents import parse as parse_user_agent

from app.core.config import settings
from app.core.logging import logger as logging
from app.db import get_async_session
from app.db.tx_session import TxAsyncSession, get_tx_session
from app.models.campaign_tracking_session import CampaignTrackingSession
from app.models.campaigns import Campaign, CampaignStatus
from app.models.publisher import Publisher
from app.models.publisher_earnings import PublisherEarnings
from app.models.tracking_events import EventType, TrackingEvent
from app.schemas.campaign_tracking_session import (
    CampaignTrackingSessionCreate, CampaignTrackingSessionResponse)
from app.schemas.tracking_events import (TrackingEventCreate,
                                         TrackingEventResponse)
from app.utils.device_ua import get_device_type
from app.utils.ip_info_grabber import IPInfoGrabber
from app.utils.sys_logger import LogCategory, Logger, LogLevel

tracker_router = APIRouter(prefix="/track", tags=["Tracker"])

# Constants
JWT_ALGORITHM = "HS256"
RATE_LIMIT_MINUTES = 60
TRACKING_SESSION_COOKIE = "ats_v1"  # Abjad tracking session Version 1
TRACKING_SESSION_EXPIRY = timedelta(hours=1)


def create_tracking_jwt(data: dict) -> str:
    """Create a JWT token for campaign tracking."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + TRACKING_SESSION_EXPIRY
    to_encode.update({"exp": expire})
    logging.info(f"Creating tracking JWT with expiry: {expire}")
    return jwt.encode(to_encode, settings.SECRET, algorithm=JWT_ALGORITHM)


def decode_tracking_jwt(token: str) -> dict:
    """Decode and validate a tracking JWT."""
    try:
        decoded = jwt.decode(token, settings.SECRET, algorithms=[JWT_ALGORITHM])
        logging.info("Successfully decoded tracking JWT")
        return decoded
    except jwt.ExpiredSignatureError:
        logging.error("Tracking session has expired")
        raise HTTPException(status_code=401, detail="Tracking session has expired")
    except jwt.JWTError:
        logging.error("Invalid tracking session")
        raise HTTPException(status_code=401, detail="Invalid tracking session")


async def get_tracking_session(
    request: Request,
    publisher_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> CampaignTrackingSession:
    """Get and validate the tracking session from cookies."""
    jwt_token = request.cookies.get(TRACKING_SESSION_COOKIE)
    if not jwt_token:
        logging.error("Missing or invalid tracking session")
        raise HTTPException(
            status_code=401, detail="Missing or invalid tracking session"
        )

    session_data = decode_tracking_jwt(jwt_token)
    logging.info(f"Validating tracking session for data: {session_data}")
    logging.info(f"Validating tracking session for publisher: {publisher_id}")
    logging.info(f"Validating tracking session for IP: {request.client.host}")
    logging.info(
        f"Validating tracking session for user agent: {
            request.headers.get('User-Agent')}"
    )
    tracking_session = await CampaignTrackingSession.get_valid_session(
        session,
        jwt_token,
        request.client.host,
        request.headers.get("User-Agent"),
        publisher_id,
    )

    if not tracking_session:
        logging.error("DATABASE ISSUE: Invalid or expired tracking session")
        raise HTTPException(
            status_code=401, detail="Invalid or expired tracking session"
        )

    logging.info("Successfully retrieved tracking session")
    return tracking_session


async def get_tracking_session_with_publisher(
    request: Request,
    publisher_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> CampaignTrackingSession:
    """Get tracking session with publisher ID from path."""
    logging.info(f"Getting tracking session for publisher: {publisher_id}")
    return await get_tracking_session(request, publisher_id, session)


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
    # TODO: If there is an already session with the same publisher ID and IP
    # return it
    client_ip = request.client.host
    if not client_ip:
        raise HTTPException(status_code=400, detail="Missing IP address")

    user_agent = track_request.viewer_user_agent or request.headers.get("User-Agent")
    if not user_agent:
        raise HTTPException(status_code=400, detail="Missing user agent")

    if not publisher_id:
        raise HTTPException(status_code=400, detail="Missing publisher ID")

    # Parse user agent to detect bots
    parsed_user_agent = parse_user_agent(user_agent)
    if parsed_user_agent.is_bot or parsed_user_agent.is_email_client:
        raise HTTPException(status_code=403, detail="Bot traffic not allowed")

    # Create expiration time with buffer for database
    now = datetime.now(UTC)
    jwt_expiry = now + TRACKING_SESSION_EXPIRY
    # Add 1 minute buffer for database
    db_expiry = jwt_expiry + timedelta(minutes=1)
    logging.info(f"JWT expiry: {jwt_expiry}, DB expiry: {db_expiry}")

    # Create JWT with session data
    jwt_data = {
        "ip": client_ip,
        "ua": user_agent,
        "res": track_request.viewer_screen_resolution,
        "lang": track_request.viewer_language,
        "pub_id": publisher_id,
        "exp": jwt_expiry,
    }
    jwt_token = create_tracking_jwt(jwt_data)

    # Create and store session
    tracking_session = await CampaignTrackingSession.create_session(
        session,
        jwt_token,
        client_ip,
        user_agent,
        publisher_id,
        screen_resolution=track_request.viewer_screen_resolution,
        language=track_request.viewer_language,
        expires_at=db_expiry,  # Pass explicit expiry time
    )

    # Set cookie with JWT token
    response.set_cookie(
        key=TRACKING_SESSION_COOKIE,
        value=jwt_token,
        max_age=int(TRACKING_SESSION_EXPIRY.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=True if settings.DEBUG is False else None,
        domain=None,
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
    tracking_session: CampaignTrackingSession = Depends(
        get_tracking_session_with_publisher
    ),
    session: TxAsyncSession = Depends(get_tx_session),
    async_session: AsyncSession = Depends(get_async_session),
):
    """Track campaign views with JWT-based session validation and rate limiting."""
    try:
        logging.info(f"Starting campaign tracking for campaign_id: {
                     campaign_id}, publisher_id: {publisher_id}")
        client_ip = tracking_session.viewer_ip
        logging.info(f"Client IP: {client_ip}")

        time_window_checking_limit = datetime.now(UTC) - timedelta(
            minutes=RATE_LIMIT_MINUTES
        )
        logging.info(f"Time window checking limit: {
                     time_window_checking_limit}")
        logging.info(f"Checking duplicate event - IP: {client_ip}, Campaign ID: {
                     campaign_id}, Event Type: {track_request.event_type.value}")
        eventtype = track_request.event_type.value
        is_duplicate = await TrackingEvent.check_duplicate_event(
            db_session=async_session,
            viewer_ip=client_ip,
            campaign_id=campaign_id,
            event_type=eventtype,
            time_window_checking_limit=time_window_checking_limit,
        )
        logging.info(f"Duplicate event check result: {is_duplicate}")
        if is_duplicate:
            logging.warning(f"Duplicate event detected for IP: {
                            client_ip}, Campaign ID: {campaign_id}")
            raise HTTPException(
                status_code=429,
                detail=f"Duplicate event detected. Please wait {
                    RATE_LIMIT_MINUTES} minutes between events.",
            )

        logging.info("Fetching IP info for geolocation")
        ip_info_grabber = IPInfoGrabber()
        ip_info = ip_info_grabber.get_ip_info(client_ip, debug=settings.DEBUG)
        logging.info(f"IP info: {ip_info}")

        logging.info(f"Fetching publisher info for publisher_id: {publisher_id}")
        publisher = await Publisher.get(async_session, publisher_id)
        if not publisher:
            logging.error(f"Publisher not found for publisher_id: {publisher_id}")
            raise HTTPException(status_code=404, detail="Publisher not found")
        logging.info("Publisher found successfully")

        logging.info("Parsing user agent")
        ua = parse_ua(tracking_session.viewer_user_agent)
        device = getattr(ua.device, "brand", "Unknown")
        os = getattr(ua.os, "family", "Unknown")
        browser = getattr(ua.user_agent, "family", "Unknown")
        logging.info(
            f"Parsed user agent - Device: {device}, OS: {os}, Browser: {browser}"
        )

        logging.info(f"Fetching campaign info for campaign_id: {campaign_id}")
        # TODO: Lazy and ugly solution fix later I'M LOOSING MY MIND :P
        # NOTE: Move to model class
        campaign_result = await async_session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign: Campaign = campaign_result.scalars().first()
        if not campaign or campaign.campaign_status != CampaignStatus.ACTIVE:
            logging.error(
                f"Invalid campaign or publisher for campaign_id: {campaign_id}"
            )
            raise ValueError("Invalid campaign or publisher")
        logging.info(f"Campaign found and active: {campaign_id}")

        logging.info("Creating tracking event")
        tracking_event = await TrackingEvent.create_event(
            db_session=async_session,
            campaign_id=campaign_id,
            ip_info=ip_info,
            device=device,
            device_type=get_device_type(tracking_session.viewer_user_agent),
            os=os,
            ad_id=campaign.advertisement_id,
            language=tracking_session.viewer_language,
            browser=browser,
            tracking_session_id=tracking_session.id,
            user_agent=tracking_session.viewer_user_agent,
            publisher_id=publisher_id,
            event_type=eventtype,
            screen_resolution=tracking_session.viewer_screen_resolution,
        )
        logging.info(f"Tracking event created: {tracking_event}")

        earnings_details = {
            "total_earnings": tracking_event.earnings,
            "publisher_earnings": tracking_event.publisher_earnings,
            "platform_earnings": tracking_event.platform_earnings,
        }
        logging.info(f"Earnings details: {earnings_details}")

        logging.info("Updating campaign budget")
        await campaign.increase_budget_used(async_session, tracking_event.earnings)
        logging.info(f"Campaign budget updated for campaign_id: {campaign_id}")

        now = datetime.now(UTC)
        views = 1 if track_request.event_type.value == EventType.VIEW.value else 0
        clicks = 1 if track_request.event_type.value == EventType.CLICK.value else 0
        impressions = (
            1 if track_request.event_type.value == EventType.IMPRESSION.value else 0
        )
        logging.info("Updating publisher earnings")
        await PublisherEarnings.create_or_update_earnings(
            db_session=async_session,
            month=now,
            views=views,
            clicks=clicks,
            impressions=impressions,
            gross_revenue=earnings_details["total_earnings"],
            platform_share=earnings_details["platform_earnings"],
            publisher_share=earnings_details["publisher_earnings"],
            publisher_id=publisher_id,
        )
        logging.info(f"Publisher earnings updated for publisher_id: {publisher_id}")

        logging.info("Logging tracking event in system log")
        log = Logger(async_session)
        await log.log(
            LogLevel.INFO,
            LogCategory.TRACKING,
            f"Processed tracking event for campaign {campaign_id} with earnings details: {earnings_details}",
            event_metadata={
                "tracking_event_id": tracking_event.id,
                "campaign_id": campaign_id,
                "publisher_id": publisher_id,
                "event_type": track_request.event_type.value
                if track_request and track_request.event_type
                else None,
                "earnings_details": earnings_details,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        logging.info("Preparing response data")
        response_data = TrackingEventResponse()

        logging.info("Cleaning up old blacklisted sessions")
        await CampaignTrackingSession.cleanup_blacklist(session)

        logging.info("Tracking process completed successfully")
        return response_data

    except Exception as e:
        logging.error(f"Error tracking campaign: {str(e)}")
        log = Logger(async_session)
        await log.log(
            LogLevel.ERROR,
            LogCategory.TRACKING,
            f"Error tracking campaign: {str(e)}",
            event_metadata={
                "campaign_id": campaign_id,
                "publisher_id": publisher_id,
                "event_type": track_request.event_type.value
                if track_request and track_request.event_type
                else None,
            },
            error=e,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error processing tracking event",
                "campaign_id": campaign_id,
                "publisher_id": publisher_id,
                "event_type": track_request.event_type.value
                if track_request and track_request.event_type
                else None,
            },
        )
