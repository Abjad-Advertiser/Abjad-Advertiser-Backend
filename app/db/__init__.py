import time
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.db_session import AsyncSessionLocal, Base, engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_db():
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
        await db.aclose()


async def database_health_check():
    """
    Health check function to verify database connectivity.
    Returns a dictionary with details about the response time and status.
    """
    start_time = time.time()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        response_time_seconds = time.time() - start_time
        response_time_microseconds = response_time_seconds * 1_000_000
        return {
            "reachable": True,
            "response_time_seconds": response_time_seconds,
            "response_time_microseconds": response_time_microseconds,
        }
    except OperationalError as e:
        logger.error(f"Database health check failed: {e}")
        response_time_seconds = time.time() - start_time
        response_time_microseconds = response_time_seconds * 1_000_000
        return {
            "reachable": False,
            "response_time_seconds": response_time_seconds,
            "response_time_microseconds": response_time_microseconds,
            "error": str(e),
        }


async def create_db_and_tables():
    """
    Creates database tables if they don't exist and updates existing tables with new columns.
    This function is a safe way to create tables and add new columns without dropping the existing database.
    It is intended to be called during application startup.

    The function does the following:
    1. Creates all tables that don't exist using `metadata.create_all()`
    2. Gets all model tables using `metadata.tables`
    3. For each table, it checks if the table exists and gets the existing columns using `get_columns()`
    4. For each table, it adds new columns that don't exist in the table using `ALTER TABLE ADD COLUMN`
    5. Logs the results of the operation
    """
    async with engine.begin() as conn:
        # Create tables that don't exist
        await conn.run_sync(Base.metadata.create_all)

        # Get all model tables
        metadata_tables = Base.metadata.tables

        # Update existing tables with new columns
        for table_name, table in metadata_tables.items():
            # Check if table exists and get columns using run_sync
            has_table = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.has_table(sync_conn, table_name)
            )

            if has_table:
                # Get existing columns using run_sync
                existing_columns = await conn.run_sync(
                    lambda sync_conn: {
                        col["name"]: col
                        for col in sync_conn.dialect.get_columns(sync_conn, table_name)
                    }
                )

                # Get desired columns from models
                model_columns = {col.name: col for col in table.columns}

                # Add new columns
                for col_name, col in model_columns.items():
                    if col_name not in existing_columns:
                        column_type = col.type.compile(engine.dialect)
                        nullable = "NULL" if col.nullable else "NOT NULL"
                        default = (
                            f"DEFAULT {
                                col.default.arg}"
                            if col.default is not None and col.default.arg is not None
                            else ""
                        )

                        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {
                            col_name} {column_type} {nullable} {default}"
                        await conn.execute(text(alter_stmt))
                        logger.info(
                            f"Added new column {col_name} to table {table_name}"
                        )

    logger.info("Database tables created or updated safely.")
