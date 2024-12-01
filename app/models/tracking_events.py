from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, String, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger as logging
from app.db.db_session import Base
from app.utils.cuid import generate_cuid
from app.utils.ip_info_grabber import IPInformation
from app.utils.pricing import PricingManager


class EventType(Enum):
    """Types of tracking events."""

    IMPRESSION = "impression"
    CLICK = "click"
    VIEW = "view"


class TrackingEvent(Base):
    """Model for tracking ad interactions."""

    __tablename__ = "tracking_events"

    id = Column(String, primary_key=True, autoincrement=False, default=generate_cuid)
    ad_id = Column(String, ForeignKey("advertisements.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    event_type = Column(SQLEnum(EventType), nullable=False)
    event_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    # Earnings tracking
    earnings = Column(Float, default=0.0, nullable=False)
    platform_earnings = Column(Float, default=0.0, nullable=False)
    publisher_earnings = Column(Float, default=0.0, nullable=False)
    # IPv4/IPv6 address of viewer
    viewer_ip = Column(String(45), nullable=False)
    # ISO 3166-1 alpha-2 country code
    viewer_country = Column(String(25), nullable=False)
    # Device (Mac, iPhone, ...)
    viewer_device = Column(String(50), nullable=False)
    # Device type (desktop, mobile, tablet, ...)
    viewer_device_type = Column(String(50), nullable=False)
    # Operating system name and version
    viewer_os = Column(String(50), nullable=False)
    # Browser name and version
    viewer_browser = Column(String(50), nullable=False)
    # ISO 639-1 language code with region
    viewer_language = Column(String(10), nullable=False)
    # Complete user agent string
    viewer_user_agent = Column(String(500), nullable=False)
    # Unique session identifier
    viewer_session_id = Column(String(128), nullable=False)
    # Resolution in WxH format (e.g. 1920x1080)
    viewer_screen_resolution = Column(String(20), nullable=False)
    # IANA timezone identifier
    viewer_timezone = Column(String(50), nullable=False)
    # Last view timestamp for rate limiting
    last_view_timestamp = Column(DateTime(timezone=True), nullable=False)
    # Publisher ID
    publisher_id = Column(String, ForeignKey("publishers.id"), nullable=True)

    @classmethod
    async def calculate_earnings(
        cls,
        event_type: EventType,
        country_code: str,
        device_type: str,
    ) -> dict[str, float]:
        """Calculate earnings for an event based on pricing configuration.

        Args:
            event_type: Type of event (impression, click, view)
            country_code: ISO 3166-1 alpha-2 country code
            device_type: Type of device (mobile, tablet, desktop)

        Returns:
            Dict containing total earnings and share breakdowns
        """
        pricing_manager = PricingManager()

        # Calculate base earnings using pricing manager
        revenue_details = pricing_manager.calculate_revenue(
            country_code=country_code,
            interaction_type=event_type,
            device_type=device_type,
        )

        earnings = revenue_details["final_rate"]

        # Calculate shares
        platform_earnings = earnings * settings.PLATFORM_SHARE
        publisher_earnings = earnings * settings.PUBLISHER_SHARE

        return {
            "earnings": earnings,
            "platform_earnings": platform_earnings,
            "publisher_earnings": publisher_earnings,
            "currency": revenue_details["currency"],
        }

    @classmethod
    async def create_event(
        cls,
        db_session: AsyncSession,
        ad_id: str,
        campaign_id: str,
        event_type: EventType,
        ip_info: IPInformation,
        device: str,
        device_type: str,
        os: str,
        browser: str,
        language: str,
        tracking_session_id: str,
        user_agent: str,
        publisher_id: str,
        screen_resolution: str,
    ) -> "TrackingEvent":
        """Create a new tracking event

        Args:
            db_session: Database session
            ad_id: ID of the advertisement
            campaign_id: ID of the campaign
            event_type: Type of event (impression, click, view)
            ip_info: Information about the viewer's IP
            device: Device name
            device_type: Type of device (mobile, desktop, etc)
            os: Operating system
            browser: Browser name
            language: Viewer's language
            tracking_session_id: ID of the tracking session
            user_agent: User agent string
            publisher_id: ID of the publisher

        Returns:
            The created tracking event
        """
        # Calculate earnings using the pricing manager
        earnings_details = await cls.calculate_earnings(
            event_type=event_type,
            country_code=ip_info.country,
            device_type=device_type,
        )

        event = cls(
            ad_id=ad_id,
            campaign_id=campaign_id,
            event_type=event_type,
            earnings=earnings_details["earnings"],
            platform_earnings=earnings_details["platform_earnings"],
            publisher_earnings=earnings_details["publisher_earnings"],
            viewer_ip=ip_info.ip,
            viewer_country=ip_info.country,
            viewer_device=device,
            viewer_device_type=device_type,
            viewer_os=os,
            viewer_browser=browser,
            viewer_language=language,
            viewer_user_agent=user_agent,
            viewer_session_id=tracking_session_id,
            viewer_screen_resolution=screen_resolution,
            viewer_timezone=ip_info.timezone,
            publisher_id=publisher_id,
            last_view_timestamp=datetime.now(UTC),
        )
        db_session.add(event)

        await db_session.commit()
        return event

    @classmethod
    async def check_duplicate_event(
        cls,
        db_session: AsyncSession,
        campaign_id: str,
        viewer_ip: str,
        event_type: EventType,
        time_window_checking_limit: datetime,
    ) -> bool:
        """Check if a duplicate event exists within the time window.

        This method implements time-based duplicate detection using a sliding window:

        Timeline Legend:
        --------------
        [TWL] = time_window_checking_limit (Now - 60min)
        [Now] = Current time
        [E#]  = Event occurrence
        [✓]   = Event outside window (allowed)
        [×]   = Event inside window (blocked)

        Time Window Examples:
        ------------------

        1) Event Outside Window (Allowed):

            Past [TWL]      [Now] Future
        .....|....|..........|....→
             E1   |          |
             ✓    |          |
                  |          |
            Result: False (Allow new event)

        2) Event Inside Window (Blocked):

            Past [TWL]      [Now] Future
        .....|....|..........|....→
                  |    E2    |
                  |    ×     |
                  |          |
            Result: True (Block new event)

        3) Multiple Events:

            Past [TWL]      [Now] Future
        .....|....|..........|....→
             E1   |  E2  E3  |
             ✓    |   ×   ×  |
                  |          |
            Result: True (Block new event)

        4) Request in future:

             Past [TWL]      [Now] Future
        .....|....|..........|....→
             E1   |  E2  E3  |       E4
             ✓    |   ×   ×  |       ✓
                  |          |
            Result: False (Allow new event)

        Args:
        ----
        db_session: Database session
        campaign_id: ID of the campaign
        viewer_ip: IP address of the viewer
        event_type: Type of event (impression, click, view)
        time_window_checking_limit: Timestamp to check for duplicate events

        Query Logic:
        -----------
        - Checks: campaign_id, viewer_ip, event_type match
        - Time: event.timestamp >= time_window_checking_limit
        - Limit: 1 (stops after finding first match)

        Returns:
        -------
        - True: Found event inside window (block)
        - False: No events inside window (allow)
        """
        logging.info(f"(INSIDE) Checking duplicate event - IP: {
                     viewer_ip}, Campaign ID: {campaign_id}, Event Type: {event_type}")
        result = await db_session.execute(
            select(cls)
            .where(
                and_(
                    cls.campaign_id == campaign_id,
                    cls.viewer_ip == viewer_ip,
                    cls.event_type == event_type,
                    cls.last_view_timestamp >= time_window_checking_limit,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
