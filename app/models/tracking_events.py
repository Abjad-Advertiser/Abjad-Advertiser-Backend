from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, String, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.db_session import Base
from app.models.campaigns import Campaign
from app.models.publisher_earnings import PublisherEarnings
from app.utils.cuid import generate_cuid
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
    event_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    # Earnings tracking
    earnings = Column(Float, default=0.0, nullable=False)
    platform_earnings = Column(Float, default=0.0, nullable=False)
    publisher_earnings = Column(Float, default=0.0, nullable=False)
    # IPv4/IPv6 address of viewer
    viewer_ip = Column(String(45), nullable=False)
    # ISO 3166-1 alpha-2 country code
    viewer_country = Column(String(2), nullable=False)
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
    publisher_id = Column(String, ForeignKey("publishers.id"), nullable=False)

    @classmethod
    async def check_rate_limit(
        cls,
        session: AsyncSession,
        viewer_ip: str,
        campaign_id: str,
        rate_limit_minutes: int,
    ) -> tuple[bool, "TrackingEvent | None"]:
        """Check if viewer has exceeded rate limit.
        Returns (is_rate_limited, last_view_event).
        """
        rate_limit_time = datetime.now(UTC) - timedelta(minutes=rate_limit_minutes)
        query = select(cls).where(
            and_(
                cls.viewer_ip == viewer_ip,
                cls.event_type == EventType.VIEW,
                cls.last_view_timestamp >= rate_limit_time,
            )
        )
        result = await session.execute(query)
        recent_view = result.scalar_one_or_none()

        if recent_view and str(recent_view.campaign_id) != campaign_id:
            return True, recent_view
        return False, recent_view

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
            interaction_type=event_type.value,
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
        event_data: dict[str, Any],
    ) -> "TrackingEvent":
        """Create a new tracking event

        Args:
            db_session: Database session
            ad_id: ID of the advertisement
            campaign_id: ID of the campaign
            event_type: Type of event (impression, click, view)
            event_data: Dictionary containing event data

        Returns:
            The created tracking event
        """
        # Calculate earnings using the pricing manager
        earnings_details = await cls.calculate_earnings(
            event_type=event_type,
            country_code=event_data["viewer_country"],
            device_type=event_data["viewer_device_type"],
        )

        event = cls(
            ad_id=ad_id,
            campaign_id=campaign_id,
            event_type=event_type,
            earnings=earnings_details["earnings"],
            platform_earnings=earnings_details["platform_earnings"],
            publisher_earnings=earnings_details["publisher_earnings"],
            **event_data,
        )
        db_session.add(event)

        # Get the publisher ID from the campaign
        campaign_result = await db_session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = campaign_result.scalars().first()
        if not campaign or not campaign.publisher_id:
            raise ValueError("Invalid campaign or publisher")

        # Update publisher earnings
        now = datetime.now(UTC)
        views = 1 if event_type == EventType.VIEW else 0
        clicks = 1 if event_type == EventType.CLICK else 0
        impressions = 1 if event_type == EventType.IMPRESSION else 0

        await PublisherEarnings.create_or_update_earnings(
            db_session,
            campaign.publisher_id,
            now,
            views=views,
            clicks=clicks,
            impressions=impressions,
            revenue=earnings_details["earnings"],
        )

        await db_session.commit()
        return event
