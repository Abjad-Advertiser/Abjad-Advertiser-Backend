import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from app.models.users import User, get_user_db
from app.core.config import settings


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    UserManager is responsible for managing user-related operations such as registration,
    password reset, and email verification.

    Attributes:
        reset_password_token_secret (str): Secret key used for generating reset password tokens.
        verification_token_secret (str): Secret key used for generating verification tokens.
    """
    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Called after a user has successfully registered.

        Args:
            user (User): The user that has registered.
            request (Optional[Request]): The request object, if available.
        """
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """
        Called after a user has requested a password reset.

        Args:
            user (User): The user that has requested a password reset.
            token (str): The reset token generated for the user.
            request (Optional[Request]): The request object, if available.
        """
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """
        Called after a user has requested email verification.

        Args:
            user (User): The user that has requested verification.
            token (str): The verification token generated for the user.
            request (Optional[Request]): The request object, if available.
        """
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    """
    Dependency that provides an instance of UserManager.

    Args:
        user_db: The user database dependency.

    Yields:
        UserManager: An instance of UserManager.
    """
    yield UserManager(user_db)