from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, CookieTransport

from app.models.sessions import get_database_strategy
from app.models.users import get_user_db

# Cookie transport configuration
# This defines how the session ID is transmitted in HTTP requests via cookies.
cookie_transport = CookieTransport(cookie_max_age=3600)

# Authentication backend configuration
# This section configures the authentication backend, specifying how
# sessions are managed.
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