from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import logger

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

max_retries = 20
for attempt in range(max_retries):
    try:
        logger.info(f"Database URL: {SQLALCHEMY_DATABASE_URL}")
        engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
        AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        break  # Exit the loop if successful
    except Exception as e:
        logger.error(f"Error creating engine: {e}")
        if attempt > max_retries - 1:
            logger.critical("Max retries reached. Could not create engine.")
logger.info("Engine created successfully.")


class Base(DeclarativeBase):
    pass
