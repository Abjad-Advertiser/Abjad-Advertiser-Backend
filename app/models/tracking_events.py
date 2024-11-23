from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String

from app.db.db_session import Base
from app.utils.cuid import generate_cuid


class TrackingEvent(Base):
    id = Column(Integer, primary_key=True, autoincrement=False, default=generate_cuid)
    ad_id = Column(Integer, ForeignKey("advertisers.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    event_type = Column(Enum("impression", "click"), nullable=False)
    event_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    # IPv4/IPv6 address of viewer
    viewer_ip = Column(String(45), nullable=False)
    # ISO 3166-1 alpha-2 country code
    viewer_country = Column(String(2), nullable=False)
    # Device type (mobile, tablet, desktop)
    viewer_device = Column(String(50), nullable=False)
    # Operating system name and version
    viewer_os = Column(String(50), nullable=False)
    # Browser name and version
    viewer_browser = Column(String(50), nullable=False)
    # ISO 639-1 language code with region
    viewer_language = Column(String(10), nullable=False)
    # Complete user agent string
    viewer_user_agent = Column(String(500), nullable=False)
    viewer_session_id = Column(String(128), nullable=False)  # Unique session identifier
    # Resolution in WxH format (e.g. 1920x1080)
    viewer_screen_resolution = Column(String(20), nullable=False)
    # IANA timezone identifier
    viewer_timezone = Column(String(50), nullable=False)
