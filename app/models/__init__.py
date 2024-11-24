from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import AsyncSessionLocal, Base, engine
from app.models.users.users import User


async def create_db_and_tables_fastapi_users():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session_fastapi_users() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_db_fastapi_users(
    session: AsyncSession = Depends(get_async_session_fastapi_users),
):
    yield SQLAlchemyUserDatabase(session, User)
