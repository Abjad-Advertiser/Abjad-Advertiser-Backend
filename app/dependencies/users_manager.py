from typing import Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, InvalidID, InvalidPasswordException

from app.core.config import settings
from app.models.users import User, get_user_db
from app.schemas.users import UserCreate
from app.utils.cuid import CUID


class UserManager(BaseUserManager[User, str]):
    """
    UserManager is responsible for managing user-related operations such as registration,
    password reset, and email verification.

    Attributes:
        reset_password_token_secret (str): Secret key used for generating reset password tokens.
        verification_token_secret (str): Secret key used for generating verification tokens.
    """

    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

    def parse_id(self, value: Any) -> CUID:
        try:
            return CUID(value)
        except ValueError as e:
            raise InvalidID() from e

    async def on_after_register(self, user: User, request: Request | None = None):
        """
        Called after a user has successfully registered.

        Args:
            user (User): The user that has registered.
            request (Optional[Request]): The request object, if available.
        """
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        """
        Called after a user has requested a password reset.

        Args:
            user (User): The user that has requested a password reset.
            token (str): The reset token generated for the user.
            request (Optional[Request]): The request object, if available.
        """
        print(
            f"User {
                user.id} has forgot their password. Reset token: {token}"
        )

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        """
        Called after a user has requested email verification.

        Args:
            user (User): The user that has requested verification.
            token (str): The verification token generated for the user.
            request (Optional[Request]): The request object, if available.
        """
        print(
            f"Verification requested for user {
                user.id}. Verification token: {token}"
        )

    async def validate_password(self, password: str, user: UserCreate | User):
        """
        Validate the password for a user.

        Args:
            password (str): The password to validate.
            user (User): The user associated with the password.
        """
        v = password
        if len(v) < 8:
            raise InvalidPasswordException(
                "Password must be at least 8 characters long"
            )
        if not any(c.isupper() for c in v):
            raise InvalidPasswordException(
                "Password must contain at least one uppercase letter"
            )
        if not any(c.islower() for c in v):
            raise InvalidPasswordException(
                "Password must contain at least one lowercase letter"
            )
        if not any(c.isdigit() for c in v):
            raise InvalidPasswordException("Password must contain at least one number")
        return v


async def get_user_manager(user_db=Depends(get_user_db)):
    """
    Dependency that provides an instance of UserManager.

    Args:
        user_db: The user database dependency.

    Yields:
        UserManager: An instance of UserManager.
    """
    yield UserManager(user_db)
