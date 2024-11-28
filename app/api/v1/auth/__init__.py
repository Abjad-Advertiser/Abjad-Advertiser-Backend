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

from fastapi import APIRouter

from app.dependencies.fast_api_users import auth_backend, fastapi_users
from app.schemas.users import UserCreate, UserRead, UserUpdate

auth_router = APIRouter(tags=["Authentication"])

# Route Registration
# Configures all authentication and user management endpoints.

# Session authentication routes
auth_router.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    tags=["Authentication"],
)

# User registration routes
auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["Authentication"],
)

# Password reset functionality
auth_router.include_router(
    fastapi_users.get_reset_password_router(),
    tags=["Authentication"],
)

# Email verification routes
auth_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    tags=["Authentication"],
)

# User management routes (CRUD operations)
auth_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True),
    prefix="/users",
    tags=["Users"],
)

# TODO:
# # OAuth routes
# auth_router.include_router(
#     # TODO: Add OAuth client and backend
#     #oauth_client: Any,
#     #backend: AuthenticationBackend,
#     fastapi_users.get_oauth_router(TODO),
#     prefix="/oauth",
#     tags=["auth"]
# )
