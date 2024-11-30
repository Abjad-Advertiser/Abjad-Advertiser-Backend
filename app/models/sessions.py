from fastapi import Depends
from fastapi_users.authentication.strategy.db import (AccessTokenDatabase,
                                                      DatabaseStrategy)
from fastapi_users_db_sqlalchemy.access_token import (
    SQLAlchemyAccessTokenDatabase, SQLAlchemyBaseAccessTokenTable)
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.db import Base, get_async_session


class SessionsAccessToken(SQLAlchemyBaseAccessTokenTable[str], Base):
    """
    Access token model for storing authentication tokens.

    Inherits from SQLAlchemyBaseAccessTokenTableUUID which provides:
    - token: UUID primary key
    - created_at: Timestamp of token creation
    - user_id: Foreign key to user table

    Additional fields:
    - user: Relationship to User model
    """

    __tablename__ = "sessions"

    country = mapped_column(String, nullable=True)
    city = mapped_column(String, nullable=True)
    ip = mapped_column(String, nullable=True)
    user_agent = mapped_column(String, nullable=True)
    device = mapped_column(String, nullable=True)
    os = mapped_column(String, nullable=True)
    browser = mapped_column(String, nullable=True)
    language = mapped_column(String, nullable=True)

    @declared_attr
    def user_id(cls) -> Mapped[str]:
        return mapped_column(
            String, ForeignKey("users.id", ondelete="cascade"), nullable=False
        )


async def get_access_token_db(
    session: AsyncSession = Depends(get_async_session),
):
    yield SQLAlchemyAccessTokenDatabase(session, SessionsAccessToken)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[SessionsAccessToken] = Depends(
        get_access_token_db
    ),
) -> DatabaseStrategy:
    from datetime import timedelta

    lifetime_seconds = timedelta(weeks=2).total_seconds()  # 2 weeks in seconds
    return DatabaseStrategy(access_token_db, lifetime_seconds=lifetime_seconds)
