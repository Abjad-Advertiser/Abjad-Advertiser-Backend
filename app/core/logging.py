"""
Logging configuration module for the adserver application.

This module sets up logging with both console and file handlers. Logs are written to:
- Console (stdout) for real-time monitoring
- Rotating log files in the 'logs' directory

The log files use rotation to prevent unbounded disk usage:
- Maximum file size: 10MB
- Keeps up to 5 backup files

Log Format:
    timestamp - logger_name - log_level - message
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create public logger instance
logger = logging.getLogger("adserver")


def setup_logging():
    """
    Configure application-wide logging settings.

    This function sets up logging with both console and file handlers:
    - Console handler writes logs to stdout for real-time monitoring
    - File handler writes to rotating log files in the 'logs' directory

    The log files rotate when they reach 10MB, keeping up to 5 backup files.
    All handlers use the format:
        timestamp - logger_name - log_level - message

    Both handlers are set to INFO level.
    """
    # Only set up logging if DEBUG is True
    if os.getenv("DEBUG", "False").lower() == "true":
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        # File handler
        file_handler = RotatingFileHandler(
            log_dir / "adserver.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    else:
        # If debug is false, set logger to null handler
        logger.addHandler(logging.NullHandler())
