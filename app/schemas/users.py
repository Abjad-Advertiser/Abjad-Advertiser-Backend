from typing import Annotated

import phonenumbers
from fastapi_users import schemas
from pydantic import EmailStr, StringConstraints, field_validator

from app.models.users import UserType


class UserRead(schemas.BaseUser):
    """
    Schema for reading user data. This defines what user data can be returned in API responses.

    Extends FastAPI-Users BaseUser schema with additional custom fields:
    - username: User's unique username
    - user_type: Enum defining user role/type
    - full_name: User's full name
    - company_name: Optional company affiliation
    - phone_number: Optional contact number in E.164 format
    """

    username: str
    email: EmailStr
    user_type: UserType
    full_name: str
    company_name: str | None = None
    phone_number: str | None = None


class UserCreate(schemas.BaseUserCreate):
    """
    Schema for user registration. Defines the required and optional fields when creating a new user.

    Extends FastAPI-Users BaseUserCreate with:
    - Custom fields with validation rules
    - Role and permission flags
    - Strict validation for username, password, and contact details

    Field Constraints:
    - username: 3-50 characters
    - password: 8-255 characters with complexity requirements
    - full_name: 2-100 characters
    - company_name: Optional, 2-100 characters
    - phone_number: Optional, E.164 format validation

    Permission Flags:
    - is_active: Indicates if the user is active and can access the platform
    - is_superuser: Indicates if the user has administrative privileges
    - is_verified: Indicates if the user is trusted because the verification process is manual acceptance
    - is_publisher: Indicates if the user has content publishing rights
    - is_advertiser: Indicates if the user has advertising privileges
    """

    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=255)]
    user_type: UserType
    full_name: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    company_name: Annotated[
        str | None, StringConstraints(min_length=2, max_length=100)
    ] = None
    phone_number: Annotated[
        str | None, StringConstraints(min_length=10, max_length=20)
    ] = None
    is_active: bool = False
    is_superuser: bool = False
    is_verified: bool = False
    is_publisher: bool = False
    is_advertiser: bool = False

    @field_validator("password")
    def validate_password(cls, v):
        """
        Enforces password complexity requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number

        Args:
            v (str): Password to validate

        Returns:
            str: Validated password

        Raises:
            ValueError: With specific message about which requirement failed
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        """
        Validates and standardizes phone numbers using the phonenumbers library.

        Features:
        - International phone number validation
        - Conversion to E.164 format
        - Optional field (can be None)

        Args:
            v (str): Phone number to validate

        Returns:
            str: Formatted phone number in E.164 format

        Raises:
            ValueError: If phone number is invalid or incorrectly formatted
        """
        if v is None:
            return v
        try:
            phone_number = phonenumbers.parse(v, None)

            if not phonenumbers.is_valid_number(phone_number):
                raise ValueError("Invalid phone number")

            formatted_number = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164
            )
            return formatted_number

        except phonenumbers.NumberParseException:
            raise ValueError(
                "Invalid phone number format. Please use international format (e.g., +1234567890)"
            )


class UserUpdate(schemas.BaseUserUpdate):
    """
    Schema for updating existing user profiles.

    Defines which fields can be updated after account creation:
    - full_name: User's full name
    - company_name: Company affiliation
    - phone_number: Contact number with E.164 validation

    All fields are optional during update operations.
    """

    full_name: (
        Annotated[str, StringConstraints(min_length=2, max_length=100)] | None
    ) = None
    company_name: Annotated[
        str | None, StringConstraints(min_length=2, max_length=100)
    ] = None
    phone_number: Annotated[
        str | None, StringConstraints(min_length=10, max_length=20)
    ] = None

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        """
        Phone number validation for user updates.
        Uses same validation logic as UserCreate schema.

        Args:
            v (str): Phone number to validate

        Returns:
            str: Formatted phone number in E.164 format

        Raises:
            ValueError: If phone number is invalid or incorrectly formatted
        """
        if v is None:
            return v
        try:
            phone_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(phone_number):
                raise ValueError("Invalid phone number")
            formatted_number = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164
            )
            return formatted_number
        except phonenumbers.NumberParseException:
            raise ValueError(
                "Invalid phone number format. Please use international format (e.g., +1234567890)"
            )
