from sqlalchemy import Column, String, Enum, Boolean, DateTime
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timezone
import enum
from app.utils.cuid import generate_cuid
from app.db.db_session import Base
from sqlalchemy.orm import Session
from sqlalchemy.orm import Mapped, mapped_column
from fastapi import Depends
from app.db import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserType(str, enum.Enum):
    """Enumeration for user types."""
    ADVERTISER = "advertiser"
    PUBLISHER = "publisher"
    ADMIN = "admin"
    NORMAL = "normal"


class User(SQLAlchemyBaseUserTable[str], Base):
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
    id: Mapped[str] = mapped_column(String, primary_key=True, autoincrement=False, index=True, unique=True, default=generate_cuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(Enum(UserType), index=True, nullable=False, default=UserType.NORMAL)
    phone_number = Column(String(20), index=True, unique=True, nullable=True)
    
    # Personal/Company Info
    full_name = Column(String(100), nullable=True)
    company_name = Column(String(100), nullable=True)
    
    # Account Status
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)

    def __init__(self, **kwargs):
        """Initialize a new User instance.

        Automatically hashes the password if provided.

        Args:
            **kwargs: Keyword arguments for user attributes.

        Raises:
            ValueError: If neither password nor hashed_password is provided.
        """
        # Automatically hash password if provided
        if "password" not in kwargs and "hashed_password" not in kwargs:
            raise ValueError("Password is required to create credentials")
        
        if "password" in kwargs:
            kwargs["hashed_password"] = get_password_hash(kwargs.pop("password"))
        super().__init__(**kwargs)

    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain password against the stored hashed password.

        Args:
            plain_password (str): The plain password to verify.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return pwd_context.verify(plain_password, self.hashed_password)

    def safe_model_dump(self, include_profile: bool = False, exclude_none: bool = True) -> dict:
        """Safe dump model to dictionary with configurable options.

        Args:
            include_profile (bool): Whether to include related profile data.
            exclude_none (bool): Whether to exclude fields with None values.

        Returns:
            dict: Dictionary representation of the user model.
        """
        # Get all column names from the table
        columns = self.__table__.columns.keys()
        
        # Create base dictionary from column values, excluding hashed_password
        data = {
            col: getattr(self, col) 
            for col in columns 
            if col != "hashed_password"  # Don't include hashed password in dumps
        }
        
        # Handle special types
        for key, value in list(data.items()):  # Use list to avoid runtime modification issues
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
            elif isinstance(value, enum.Enum):
                data[key] = value.value if value else None
                
        if include_profile and self.profile:
            # Get profile data as dict, excluding None values if requested
            profile_data = {
                k: v for k, v in self.profile.__dict__.items() 
                if not k.startswith('_') and (not exclude_none or v is not None)
            }
            data["profile"] = profile_data
            
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
            
        return data


# Helper functions
def get_password_hash(password: str) -> str:
    """Hash a password using the configured hashing context.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_db(session: Session = Depends(get_db)):
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