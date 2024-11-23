"""
FastAPI Users Authentication and User Management System

This module implements a comprehensive authentication and user management system using the FastAPI-Users library.
It provides a secure, feature-rich authentication system with the following capabilities:

Key Features:
- **Database-backed session authentication**: Securely manage user sessions with a database backend.
- **User registration with email verification**: Allow users to register and verify their email addresses for added security.
- **Password reset functionality**: Enable users to reset their passwords securely.
- **User profile management**: Manage user profiles with customizable fields.
- **Role-based access control**: Implement different user roles (e.g., Publisher, Advertiser, Superuser) for access control.
- **Phone number validation**: Validate user phone numbers during registration.
- **Customizable user schemas**: Adapt user data models to fit specific application needs.

Technical Implementation:
- Utilizes the FastAPI-Users library for core authentication functionality.
- Implements database session authentication using SQLAlchemy for database operations.
- Employs Pydantic models for request and response validation, ensuring data integrity.
- Incorporates custom validation for passwords and phone numbers to enhance security.
- Supports role-based user types to facilitate different access levels within the application.

Security Features:
- **Secure password hashing**: Passwords are hashed using a secure algorithm to protect user credentials.
- **Email verification system**: Ensures that users verify their email addresses to prevent fraudulent registrations.
- **Database session management**: Manages user sessions securely within the database.
- **Password complexity requirements**: Enforces strong password policies to enhance security.
- **Input validation and sanitization**: Validates and sanitizes user input to prevent common security vulnerabilities.

"""

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from app.schemas.users import UserCreate, UserRead, UserUpdate
from app.models.users import get_user_db
from app.models.sessions import get_database_strategy
from fastapi import APIRouter
auth_router = APIRouter(tags=["Authentication"])

# Cookie transport configuration
# This defines how the session ID is transmitted in HTTP requests via cookies.
cookie_transport = CookieTransport(cookie_max_age=3600)

# Authentication backend configuration
# This section configures the authentication backend, specifying how sessions are managed.
auth_backend = AuthenticationBackend(
    name="session",  # Identifier for the authentication backend
    transport=cookie_transport,  # Defines how sessions are transmitted
    get_strategy=get_database_strategy,  # Defines how sessions are handled
)

# FastAPI Users instance configuration
# This ties together all components:
# - Database adapter
# - Authentication backend
# - User models and schemas
fastapi_users = FastAPIUsers(
    get_user_db,
    [auth_backend],
)

# Current user retrieval
# These variables provide access to the current active user and superuser.
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Route Registration
# Configures all authentication and user management endpoints.

# Session authentication routes
auth_router.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    prefix="/session",
    tags=["Authentication"]
)

# User registration routes
auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["Authentication"],
    prefix="/register"
)

# Password reset functionality
auth_router.include_router(
    fastapi_users.get_reset_password_router(),
    tags=["Authentication"],
    prefix="/password"
)

# Email verification routes
auth_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    tags=["Authentication"],
    prefix="/verify"
)

# User management routes (CRUD operations)
auth_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"]
)

#TODO:
# # OAuth routes
# auth_router.include_router(
#     # TODO: Add OAuth client and backend
#     #oauth_client: Any,
#     #backend: AuthenticationBackend,
#     fastapi_users.get_oauth_router(TODO),
#     prefix="/oauth",
#     tags=["auth"]
# )