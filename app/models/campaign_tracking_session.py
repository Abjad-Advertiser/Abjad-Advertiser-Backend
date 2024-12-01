"""Campaign tracking session model for managing JWT-based tracking sessions."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, String, Text,
                        select)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import expression

from app.db.db_session import Base
from app.utils.cuid import generate_cuid


class CampaignTrackingSession(Base):
    __tablename__ = "campaign_tracking_sessions"

    id = Column(String, primary_key=True, autoincrement=False, default=generate_cuid)
    jwt_token = Column(Text, nullable=False)
    viewer_ip = Column(String(45), nullable=False)
    viewer_user_agent = Column(String(500), nullable=False)
    viewer_screen_resolution = Column(
        String(20), nullable=True
    )  # Format: WxH (e.g. 1920x1080)
    # Format: ISO 639-1 with region (e.g. en-US)
    viewer_language = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_blacklisted = Column(Boolean, server_default=expression.false(), nullable=False)
    blacklisted_at = Column(DateTime(timezone=True), nullable=True)
    publisher_id = Column(String, ForeignKey("publishers.id"), nullable=False)

    @classmethod
    async def create_session(
        cls,
        session: AsyncSession,
        jwt_token: str,
        ip: str,
        user_agent: str,
        publisher_id: str,
        screen_resolution: str | None = None,
        language: str | None = None,
        expires_at: datetime | None = None,
    ) -> "CampaignTrackingSession":
        """Create a new tracking session."""
        tracking_session = cls(
            jwt_token=jwt_token,
            viewer_ip=ip,
            viewer_user_agent=user_agent,
            viewer_screen_resolution=screen_resolution,
            viewer_language=language,
            expires_at=expires_at or (datetime.now(UTC) + timedelta(hours=1)),
            publisher_id=publisher_id,
        )
        session.add(tracking_session)
        await session.commit()
        await session.refresh(tracking_session)
        return tracking_session

    @classmethod
    async def get_valid_session(
        cls,
        session: AsyncSession,
        jwt_token: str,
        ip: str,
        user_agent: str,
        publisher_id: str,
    ) -> "CampaignTrackingSession | None":
        """Get a valid session by JWT token and validate IP and user agent."""
        from app.core.logging import logger as logging

        logging.info(f"Querying session with token: {jwt_token}")
        logging.info(f"IP: {ip}")
        logging.info(f"User Agent: {user_agent}")
        logging.info(f"Publisher ID: {publisher_id}")

        now = datetime.now(UTC)
        logging.info(f"Current time (UTC): {now}")

        query = select(cls).where(
            cls.jwt_token == jwt_token,
            cls.viewer_ip == ip,
            cls.viewer_user_agent == user_agent,
            cls.expires_at > now,
            cls.is_blacklisted.is_(False),
            cls.publisher_id == publisher_id,
        )
        result = await session.execute(query)
        session_result = result.scalar_one_or_none()

        if session_result is None:
            # Query to find any session with this token to help debug
            debug_query = select(cls).where(cls.jwt_token == jwt_token)
            debug_result = await session.execute(debug_query)
            debug_session = debug_result.scalar_one_or_none()

            if debug_session:
                logging.error("Found session but validation failed:")
                logging.error(
                    f"Stored IP: {
                        debug_session.viewer_ip} vs Received: {ip}"
                )
                logging.error(
                    f"Stored UA: {
                        debug_session.viewer_user_agent} vs Received: {user_agent}"
                )
                logging.error(
                    f"Stored Publisher: {
                        debug_session.publisher_id} vs Received: {publisher_id}"
                )
                logging.error(
                    f"Is Blacklisted: {
                        debug_session.is_blacklisted}"
                )
                logging.error(f"Expires At (UTC): {debug_session.expires_at}")
                logging.error(f"Current Time (UTC): {now}")
            else:
                logging.error("No session found with this token")

        return session_result

    @classmethod
    async def blacklist_session(cls, session: AsyncSession, jwt_token: str):
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
