from fastapi import Depends
from fastapi_users.authentication.strategy.db import (AccessTokenDatabase,
                                                      DatabaseStrategy)
from fastapi_users_db_sqlalchemy.access_token import (
    SQLAlchemyAccessTokenDatabase, SQLAlchemyBaseAccessTokenTableUUID)
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.db import get_async_session
from app.models import Base


class SessionsAccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    """
    Access token model for storing authentication tokens.

    Inherits from SQLAlchemyBaseAccessTokenTableUUID which provides:
    - token: UUID primary key
    - created_at: Timestamp of token creation
    - user_id: Foreign key to user table

    Additional fields:
    - user: Relationship to User model
    """

    __tablename__ = "sessions_access_token"

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
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)
