from fastapi import FastAPI
from app.api.v1.auth import auth_router
from contextlib import asynccontextmanager
from app.models import create_db_and_tables_fastapi_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.

    This function is responsible for setting up the application lifecycle.
    It creates the necessary database tables for FastAPI Users when the application starts
    and yields control back to the application. After the application is done,
    any necessary cleanup can be performed here.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    print("Available routes:")
    for route in app.routes:
        print(f"  • {route.path}")
    await create_db_and_tables_fastapi_users()
    yield

app = FastAPI(
    title="Abjad Ad Server API",
    version="1.0.0",
    description="API for serving and managing advertisements services",
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
