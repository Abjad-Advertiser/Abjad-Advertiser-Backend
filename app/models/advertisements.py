from sqlalchemy import Column, ForeignKey, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base
from app.schemas.advertisements import AdvertisementCreate, AdvertisementUpdate
from app.utils.cuid import generate_cuid

from .users import User

# TODO: Add status type to advertisement (e.g. under_ai_review,
# required_human_review, approved, rejected)


class Advertisement(Base):
    __tablename__ = "advertisements"
    id = Column(String, autoincrement=False, primary_key=True, default=generate_cuid)

    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    media = Column(String, nullable=False)
    target_audience = Column(String, nullable=False)

    user_id = Column(String, ForeignKey(User.id), nullable=False, index=True)

    @classmethod
    async def create_ad(
        cls: "Advertisement",
        session: AsyncSession,
        ad_data: AdvertisementCreate,
        user_id: str,
    ) -> "Advertisement":
        """Create a new advertisement.

        Args:
            session: The database session
            ad_data: Advertisement creation data
            user_id: ID of the user creating the advertisement

        Returns:
            Created Advertisement object
        """
        ad = cls(
            title=ad_data.title,
            description=ad_data.description,
            media=ad_data.media,
            target_audience=ad_data.target_audience,
            user_id=user_id,
        )
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        return ad

    @classmethod
    async def get_ad(
        cls: "Advertisement", session: AsyncSession, ad_id: str
    ) -> "Advertisement" | None:
        """Get an advertisement by ID.

        Args:
            session: The database session
            ad_id: ID of the advertisement to get

        Returns:
            Advertisement if found, None otherwise
        """
        result = await session.execute(select(cls).where(cls.id == ad_id))
        return result.scalars().first()

    @classmethod
    async def get_user_ads(
        cls: "Advertisement", session: AsyncSession, user_id: str
    ) -> list["Advertisement"]:
        """Get all advertisements for a user.

        Args:
            session: The database session
            user_id: ID of the user

        Returns:
            List of Advertisement objects
        """
        result = await session.execute(select(cls).where(cls.user_id == user_id))
        return list(result.scalars().all())

    async def update_ad(
        self, session: AsyncSession, ad_data: AdvertisementUpdate
    ) -> "Advertisement":
        """Update an advertisement.

        Args:
            session: The database session
            ad_data: Updated advertisement data

        Returns:
            Updated Advertisement object
        """
        if ad_data.title is not None:
            self.title = ad_data.title
        if ad_data.description is not None:
            self.description = ad_data.description
        if ad_data.media is not None:
            self.media = ad_data.media
        if ad_data.target_audience is not None:
            self.target_audience = ad_data.target_audience

        await session.commit()
        await session.refresh(self)
        return self

    async def delete_ad(self, session: AsyncSession) -> None:
        """Delete an advertisement.

        Args:
            session: The database session
        """
        await session.delete(self)
        await session.commit()

    def model_dump(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "media": self.media,
            "target_audience": self.target_audience,
        }
