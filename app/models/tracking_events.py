from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_, select

from app.db.db_session import Base
from app.utils.cuid import generate_cuid


class EventType(Enum):
    impression = "impression"
    click = "click"
    view = "view"


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, autoincrement=False, default=generate_cuid)
    ad_id = Column(Integer, ForeignKey("advertisers.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    event_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
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
        """
        Check if viewer has exceeded rate limit.
        Returns (is_rate_limited, last_view_event).
        """
        rate_limit_time = datetime.now(UTC) - timedelta(minutes=rate_limit_minutes)
        query = select(cls).where(
            and_(
                cls.viewer_ip == viewer_ip,
                cls.event_type == EventType.view,
                cls.last_view_timestamp >= rate_limit_time,
            )
        )
        result = await session.execute(query)
        recent_view = result.scalar_one_or_none()

        if recent_view and str(recent_view.campaign_id) != campaign_id:
            return True, recent_view
        return False, recent_view

    @classmethod
    async def create_view_event(
        cls,
        session: AsyncSession,
        campaign_id: str,
        ip_info: Any,
        device: str,
        device_type: str,
        os: str,
        browser: str,
        tracking_session_id: str,
        screen_resolution: str,
        timezone: str,
        user_agent: str,
        publisher_id: str,
    ) -> "TrackingEvent":
        """Create a new view tracking event."""

        # TODO: First check if campaign exists and if publisher exists

        tracking_event = cls(
            campaign_id=campaign_id,
            event_type=EventType.view,
            viewer_ip=ip_info.ip,
            viewer_country=ip_info.country,
            viewer_device=device,
            viewer_device_type=device_type,
            viewer_os=os,
            viewer_browser=browser,
            viewer_user_agent=user_agent,
            viewer_session_id=tracking_session_id,
            viewer_screen_resolution=screen_resolution,
            viewer_timezone=timezone,
            last_view_timestamp=datetime.now(UTC),
            publisher_id=publisher_id,
        )

        session.add(tracking_event)
        await session.commit()
        await session.refresh(tracking_event)

        return tracking_event
