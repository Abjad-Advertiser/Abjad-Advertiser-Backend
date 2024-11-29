from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import general_router
from app.api.v1.advertisers import advertisers_router
from app.api.v1.auth import auth_router
from app.api.v1.billing import billing_router
from app.api.v1.campaigns import campaign_router
from app.api.v1.tracker import tracker_router
from app.db import create_db_and_tables


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
        methods = ", ".join(sorted(route.methods)) if route.methods else "No methods"
        print(f"  • {methods:<20} {route.path}")
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Abjad Ad Server API",
    version="1.0.0",
    description="API for serving and managing advertisements services",
    lifespan=lifespan,
)

# Include routers
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix, tags=["Authentication"])
app.include_router(general_router, prefix=api_v1_prefix, tags=["General"])
app.include_router(advertisers_router, prefix=api_v1_prefix, tags=["Advertisers"])
app.include_router(campaign_router, prefix=api_v1_prefix, tags=["Campaigns"])
app.include_router(billing_router, prefix=api_v1_prefix, tags=["Billing"])
app.include_router(tracker_router, prefix=api_v1_prefix, tags=["Tracker"])
