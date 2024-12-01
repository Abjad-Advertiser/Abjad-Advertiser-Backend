"""Publisher model for managing ad publishers."""

from typing import Optional

from sqlalchemy import Column, Enum, ForeignKey, String, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base
from app.schemas.publisher import (PublisherCreate, PublisherUpdate,
                                   PublishingPlatform)
from app.utils.cuid import generate_cuid


class Publisher(Base):
    """Publisher model for managing ad publishers."""

    __tablename__ = "publishers"

    id = Column(String, primary_key=True, default=generate_cuid)
    publishing_platform = Column(
        Enum(PublishingPlatform),
        nullable=False,
    )

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
