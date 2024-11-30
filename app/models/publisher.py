"""Publisher model for managing ad publishers."""

from typing import Optional

from sqlalchemy import Column, Enum, Float, ForeignKey, String, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.db import Base
from app.schemas.publisher import (PublisherCreate, PublisherUpdate,
                                   PublishingPlatform)
from app.utils.cuid import generate_cuid


class Publisher(Base):
    """Publisher model for managing ad publishers."""

    __tablename__ = "publishers"

    id = Column(String, primary_key=True, default=generate_cuid)
    revenue = Column(Float, default=0.0)
    publishing_platform = Column(
        Enum(PublishingPlatform),
        nullable=False,
    )

    # Relationships
    campaigns = relationship("Campaign", back_populates="publisher")
    tracking_events = relationship("TrackingEvent", back_populates="publisher")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    @classmethod
    async def create(
        cls, session: AsyncSession, user_id: str, data: PublisherCreate
    ) -> "Publisher":
        """Create a new publisher.

        Args:
            session: Database session
            data: Publisher creation data

        Returns:
            Created publisher instance
        """
        publisher = cls(
            publishing_platform=data.publishing_platform,
            user_id=user_id,
        )
        session.add(publisher)
        await session.commit()
        await session.refresh(publisher)
        return publisher

    @classmethod
    async def get(
        cls, session: AsyncSession, publisher_id: str
    ) -> Optional["Publisher"]:
        """Get a publisher by ID.

        Args:
            session: Database session
            publisher_id: ID of the publisher to get

        Returns:
            Publisher if found, None otherwise
        """
        result = await session.execute(select(cls).where(cls.id == publisher_id))
        return result.scalars().first()

    @classmethod
    async def get_all(
        cls, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list["Publisher"]:
        """Get all publishers with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of publishers
        """
        result = await session.execute(select(cls).offset(skip).limit(limit))
        return result.scalars().all()

    @classmethod
    async def get_user_publishers(
        cls, session: AsyncSession, user_id: str, skip: int = 0, limit: int = 100
    ) -> list["Publisher"]:
        """Get all publishers for a specific user."""
        result = await session.execute(
            select(cls).where(cls.user_id == user_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_user_publisher(
        cls, session: AsyncSession, user_id: str, publisher_id: str
    ) -> Optional["Publisher"]:
        """Get a specific publisher for a user."""
        result = await session.execute(
            select(cls).where(and_(cls.id == publisher_id, cls.user_id == user_id))
        )
        return result.scalars().first()

    async def update(self, session: AsyncSession, data: PublisherUpdate) -> "Publisher":
        """Update publisher details.

        Args:
            session: Database session
            data: Publisher update data

        Returns:
            Updated publisher instance
        """
        if data.publishing_platform is not None:
            self.publishing_platform = data.publishing_platform

        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete the publisher.

        Args:
            session: Database session
        """
        await session.delete(self)
        await session.commit()

    async def update_revenue(self, session: AsyncSession, amount: float) -> "Publisher":
        """Update publisher's revenue.

        Args:
            session: Database session
            amount: Amount to add to revenue

        Returns:
            Updated publisher instance
        """
        self.revenue += amount
        await session.commit()
        await session.refresh(self)
        return self

    async def get_stats(self, session: AsyncSession) -> dict:
        """Get publisher statistics.

        Args:
            session: Database session

        Returns:
            Dictionary containing publisher statistics
        """
        # Get tracking events for this publisher
        result = await session.execute(select(self.tracking_events))
        events = result.scalars().all()

        # Calculate statistics
        total_impressions = sum(1 for e in events if e.event_type == "impression")
        total_clicks = sum(1 for e in events if e.event_type == "click")
        total_views = sum(1 for e in events if e.event_type == "view")

        # Calculate CTR (Click-Through Rate)
        ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0

        # Group revenue by country
        revenue_by_country = {}
        for event in events:
            country = event.viewer_country
            if country not in revenue_by_country:
                revenue_by_country[country] = 0
            # Note: You'll need to implement actual revenue calculation per event
            # This is just a placeholder
            revenue_by_country[country] += event.revenue

        return {
            "total_revenue": self.revenue,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_views": total_views,
            "average_ctr": ctr,
            "revenue_by_platform": {self.publishing_platform: self.revenue},
            "revenue_by_country": revenue_by_country,
        }
