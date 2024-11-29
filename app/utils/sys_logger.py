"""Utility for system-wide logging."""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logs import LogCategory, LogLevel, SystemLog


class Logger:
    """Utility class for system-wide logging."""

    def __init__(self, session: AsyncSession):
        """Initialize logger.

        Args:
            session: Database session
        """
        self.session = session

    async def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        event_metadata: dict[str, Any] | None = None,
        error: Exception | None = None,
        request: Request | None = None,
        user_id: str | None = None,
    ) -> SystemLog:
        """Create a log entry.

        Args:
            level: Log level
            category: Log category
            message: Main log message
            event_metadata: Additional structured data
            error: Exception if logging an error
            request: FastAPI request object if available
            user_id: User ID if available

        Returns:
            Created log entry
        """
        # Extract request information if available
        request_id = None
        ip_address = None
        endpoint = None

        if request:
            request_id = request.headers.get("X-Request-ID")
            ip_address = request.client.host
            endpoint = f"{request.method} {request.url.path}"

        return await SystemLog.create_log(
            session=self.session,
            level=level,
            category=category,
            message=message,
            event_metadata=event_metadata,
            error=error,
            request_id=request_id,
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
        )

    async def debug(
        self,
        category: LogCategory,
        message: str,
        **kwargs,
    ) -> SystemLog:
        """Create a debug log entry."""
        return await self.log(LogLevel.DEBUG, category, message, **kwargs)

    async def info(
        self,
        category: LogCategory,
        message: str,
        **kwargs,
    ) -> SystemLog:
        """Create an info log entry."""
        return await self.log(LogLevel.INFO, category, message, **kwargs)

    async def warning(
        self,
        category: LogCategory,
        message: str,
        **kwargs,
    ) -> SystemLog:
        """Create a warning log entry."""
        return await self.log(LogLevel.WARNING, category, message, **kwargs)

    async def error(
        self,
        category: LogCategory,
        message: str,
        **kwargs,
    ) -> SystemLog:
        """Create an error log entry."""
        return await self.log(LogLevel.ERROR, category, message, **kwargs)

    async def critical(
        self,
        category: LogCategory,
        message: str,
        **kwargs,
    ) -> SystemLog:
        """Create a critical log entry."""
        return await self.log(LogLevel.CRITICAL, category, message, **kwargs)
