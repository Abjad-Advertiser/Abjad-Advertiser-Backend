import enum
from datetime import UTC, datetime

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db import get_async_session
from app.db.db_session import Base
from app.utils.cuid import CUID, generate_cuid

# Password hashing context


class UserType(str, enum.Enum):
    """Enumeration for user types."""

    ADVERTISER = "ADVERTISER"
    PUBLISHER = "PUBLISHER"
    GUEST = "GUEST"


class User(SQLAlchemyBaseUserTable[CUID], Base):
    """User model representing a user in the system.

    Attributes:
        id (str): Unique identifier for the user.
        username (str): Unique username for the user.
        email (str): Unique email address for the user.
        hashed_password (str): Hashed password for the user.
        user_type (UserType): Type of user (e.g., advertiser, publisher).
        phone_number (str): Optional phone number of the user.
        full_name (str): Optional full name of the user.
        company_name (str): Optional company name of the user.
        is_active (bool): Indicates if the user account is active.
        is_verified (bool): Indicates if the user account is verified.
        created_at (datetime): Timestamp of when the user was created.
        last_login (datetime): Timestamp of the last login.
    """

    __tablename__ = "users"

    # Account credentials info
    id: Mapped[CUID] = mapped_column(
        String,
        primary_key=True,
        autoincrement=False,
        index=True,
        unique=True,
        default=generate_cuid,
    )
    username = Column(String, unique=True, index=True, nullable=False)
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType, name="usertype", create_constraint=True, validate_strings=True),
        index=True,
        nullable=False,
        default=UserType.GUEST,
    )
    phone_number = Column(String(20), index=True, unique=True, nullable=True)

    # Personal
    full_name = Column(String(100), nullable=False)

    # Company Info
    company_name = Column(String(100), nullable=True)
    company_address = Column(String(100), nullable=True)
    company_website = Column(String(100), nullable=True)
    company_description = Column(String(100), nullable=True)
    company_logo = Column(String(100), nullable=True)

    # Account Status
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_login = Column(DateTime(timezone=True))


async def get_user_db(session: Session = Depends(get_async_session)):
    """FastAPI-Users database adapter dependency.

    Creates a FastAPI-Users compatible database adapter using:
    - SQLAlchemy session
    - User model

    Args:
        session (Session): Database session from get_db dependency

    Yields:
        SQLAlchemyUserDatabase: Database adapter for user operations
    """
    yield SQLAlchemyUserDatabase(session, User)
