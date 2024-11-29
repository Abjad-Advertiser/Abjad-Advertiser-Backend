"""Campaign tracking session model for managing JWT-based tracking sessions."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import expression

from app.db.db_session import Base
from app.utils.cuid import generate_cuid


class CampaignTrackingSession(Base):
    __tablename__ = "campaign_tracking_sessions"

    id = Column(String(128), primary_key=True, default=generate_cuid)
    jwt_token = Column(Text, nullable=False)
    viewer_ip = Column(String(45), nullable=False)
    viewer_user_agent = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime, nullable=False)
    is_blacklisted = Column(Boolean, server_default=expression.false(), nullable=False)
    blacklisted_at = Column(DateTime, nullable=True)

    @classmethod
    async def create_session(
        cls, session, jwt_token: str, ip: str, user_agent: str
    ) -> "CampaignTrackingSession":
        """Create a new tracking session."""
        tracking_session = cls(
            jwt_token=jwt_token,
            viewer_ip=ip,
            viewer_user_agent=user_agent,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        session.add(tracking_session)
        await session.commit()
        await session.refresh(tracking_session)
        return tracking_session

    @classmethod
    async def get_valid_session(
        cls, session, jwt_token: str, ip: str, user_agent: str
    ) -> "CampaignTrackingSession | None":
        """Get a valid session by JWT token and validate IP and user agent."""
        from sqlalchemy import select

        query = select(cls).where(
            cls.jwt_token == jwt_token,
            cls.viewer_ip == ip,
            cls.viewer_user_agent == user_agent,
            cls.expires_at > datetime.now(UTC),
            cls.is_blacklisted is False,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def blacklist_session(cls, session, jwt_token: str):
        """Blacklist a session."""
        from sqlalchemy import update

        query = (
            update(cls)
            .where(cls.jwt_token == jwt_token)
            .values(is_blacklisted=True, blacklisted_at=datetime.now(UTC))
        )
        await session.execute(query)
        await session.commit()

    @classmethod
    async def cleanup_blacklist(cls, session):
        """Remove blacklist for IPs that have been blacklisted for more than an hour."""
        from sqlalchemy import update

        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        query = (
            update(cls)
            .where(cls.is_blacklisted is True, cls.blacklisted_at <= one_hour_ago)
            .values(is_blacklisted=False, blacklisted_at=None)
        )
        await session.execute(query)
        await session.commit()
