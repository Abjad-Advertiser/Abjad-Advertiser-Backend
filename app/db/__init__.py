from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import AsyncSessionLocal


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_db():
    """
    Database session dependency provider.

    Implements a context manager pattern for database sessions:
    1. Creates a new database session
    2. Yields it for use in route handlers
    3. Ensures proper cleanup after request completion

    Yields:
        Session: SQLAlchemy database session
    """
    db = get_async_session()
    try:
        yield db
    finally:
        db.close()
