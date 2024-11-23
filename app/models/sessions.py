from sqlalchemy import ForeignKey, String
from fastapi_users_db_sqlalchemy.access_token import (
    SQLAlchemyAccessTokenDatabase,
    SQLAlchemyBaseAccessTokenTableUUID,
)
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Base
from fastapi import Depends
from app.db import get_async_session
from fastapi_users.authentication.strategy.db import AccessTokenDatabase, DatabaseStrategy

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
        return mapped_column(String, ForeignKey("users.id", ondelete="cascade"), nullable=False)


async def get_access_token_db(
    session: AsyncSession = Depends(get_async_session),
):  
    yield SQLAlchemyAccessTokenDatabase(session, SessionsAccessToken)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[SessionsAccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)
