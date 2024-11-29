"""System-wide logging model for tracking events, errors, and other important information."""

import enum
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from app.db import Base
from app.utils.cuid import generate_cuid


class LogLevel(str, enum.Enum):
    """Log levels for system events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, enum.Enum):
    """Categories for different types of logs."""

    REVENUE = "revenue"
    TRACKING = "tracking"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"


class SystemLog(Base):
    """Model for storing system-wide logs."""

    __tablename__ = "system_logs"

    id = Column(String, primary_key=True, default=generate_cuid)
    timestamp = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    level = Column(Enum(LogLevel), nullable=False, index=True)
    category = Column(Enum(LogCategory), nullable=False, index=True)

    # The main log message
    message = Column(Text, nullable=False)

    # Additional structured data
    metadata = Column(JSON, nullable=True)

    # Error details if applicable
    error_type = Column(String(100), nullable=True)
    error_details = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Request context if available
    request_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    endpoint = Column(String(200), nullable=True)

    @classmethod
    async def create_log(
        cls,
        session: AsyncSession,
        level: LogLevel,
        category: LogCategory,
        message: str,
        metadata: dict[str, Any] | None = None,
        error: Exception | None = None,
        request_id: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        endpoint: str | None = None,
    ) -> "SystemLog":
        """Create a new log entry.

        Args:
            session: Database session
            level: Log level
            category: Log category
            message: Main log message
            metadata: Additional structured data
            error: Exception object if logging an error
            request_id: Request ID if available
            user_id: User ID if available
            ip_address: IP address if available
            endpoint: API endpoint if available

        Returns:
            Created log entry
        """
        log_entry = cls(
            level=level,
            category=category,
            message=message,
            metadata=metadata,
            request_id=request_id,
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
        )

        if error:
            log_entry.error_type = error.__class__.__name__
            log_entry.error_details = str(error)
            log_entry.stack_trace = getattr(error, "__traceback__", None)

        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)
        return log_entry

    @classmethod
    async def get_logs(
        cls,
        session: AsyncSession,
        level: LogLevel | None = None,
        category: LogCategory | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list["SystemLog"]:
        """Get logs with optional filtering.

        Args:
            session: Database session
            level: Filter by log level
            category: Filter by category
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            user_id: Filter by user ID
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of log entries
        """
        query = select(cls).order_by(cls.timestamp.desc())

        if level:
            query = query.where(cls.level == level)
        if category:
            query = query.where(cls.category == category)
        if start_time:
            query = query.where(cls.timestamp >= start_time)
        if end_time:
            query = query.where(cls.timestamp <= end_time)
        if user_id:
            query = query.where(cls.user_id == user_id)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def cleanup_old_logs(
        cls,
        session: AsyncSession,
        days_to_keep: int = 30,
        exclude_levels: list[LogLevel] | None = None,
    ) -> int:
        """Clean up old log entries.

        Args:
            session: Database session
            days_to_keep: Number of days of logs to keep
            exclude_levels: Log levels to exclude from cleanup

        Returns:
            Number of deleted log entries
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)
        query = select(cls).where(cls.timestamp < cutoff_date)

        if exclude_levels:
            query = query.where(cls.level.notin_(exclude_levels))

        result = await session.execute(query)
        logs_to_delete = result.scalars().all()

        for log in logs_to_delete:
            await session.delete(log)

        await session.commit()
        return len(logs_to_delete)
