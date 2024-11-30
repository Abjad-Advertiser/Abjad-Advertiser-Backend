"""Publisher API endpoints."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.dependencies.fast_api_users import current_active_user
from app.models.publisher import Publisher
from app.models.publisher_earnings import PublisherEarnings
from app.models.users import User
from app.schemas.publisher import (PeriodicRevenue, PublisherCreate,
                                   PublisherResponse, PublisherStats,
                                   PublisherUpdate, RevenueStats)
from app.services.revenue import RevenueService

publisher_router = APIRouter(prefix="/publishers", tags=["publishers"])


@publisher_router.post("/", response_model=PublisherResponse)
async def create_publisher(
    data: PublisherCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Publisher:
    """Create a new publisher.

    Example:
        POST /api/v1/publishers/
        {
            "publishing_platform": "website"
        }

    Returns:
        {
            "id": "clh2x3e0h0000qw9k3q7q8j9k",
            "publishing_platform": "website",
            "revenue": 0.0
        }
    """
    return await Publisher.create(session, current_user.id, data)


@publisher_router.get("/", response_model=list[PublisherResponse])
async def list_user_publishers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[Publisher]:
    """Get all publishers for the current user.

    Example:
        GET /api/v1/publishers/?skip=0&limit=10

    Returns:
        [
            {
                "id": "clh2x3e0h0000qw9k3q7q8j9k",
                "publishing_platform": "website",
                "revenue": 1250.50
            },
            ...
        ]
    """
    return await Publisher.get_user_publishers(
        session, current_user.id, skip=skip, limit=limit
    )


@publisher_router.get("/{publisher_id}", response_model=PublisherResponse)
async def get_publisher(
    publisher_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Publisher:
    """Get a specific publisher by ID. Only returns publishers owned by the current user.

    Example:
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k

    Returns:
        {
            "id": "clh2x3e0h0000qw9k3q7q8j9k",
            "publishing_platform": "website",
            "revenue": 1250.50
        }

    Raises:
        404: Publisher not found or doesn't belong to current user
    """
    publisher = await Publisher.get_user_publisher(
        session, current_user.id, publisher_id
    )
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return publisher


@publisher_router.put("/{publisher_id}", response_model=PublisherResponse)
async def update_publisher(
    publisher_id: str,
    data: PublisherUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Publisher:
    """Update a publisher's details. Only updates publishers owned by the current user.

    Example:
        PUT /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k
        {
            "publishing_platform": "mobile_app"
        }

    Returns:
        {
            "id": "clh2x3e0h0000qw9k3q7q8j9k",
            "publishing_platform": "mobile_app",
            "revenue": 1250.50
        }

    Raises:
        404: Publisher not found or doesn't belong to current user
    """
    publisher = await Publisher.get_user_publisher(
        session, current_user.id, publisher_id
    )
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return await publisher.update(session, data)


@publisher_router.delete("/{publisher_id}")
async def delete_publisher(
    publisher_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete a publisher. Only deletes publishers owned by the current user.

    Example:
        DELETE /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k

    Returns:
        {
            "message": "Publisher deleted successfully"
        }

    Raises:
        404: Publisher not found or doesn't belong to current user
    """
    publisher = await Publisher.get_user_publisher(
        session, current_user.id, publisher_id
    )
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    await publisher.delete(session)
    return {"message": "Publisher deleted successfully"}


@publisher_router.get("/{publisher_id}/stats", response_model=PublisherStats)
async def get_publisher_stats(
    publisher_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get statistics for a specific publisher. Only returns stats for publishers owned by the current user.

    Example:
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k/stats

    Returns:
        {
            "total_revenue": 1250.50,
            "total_impressions": 50000,
            "total_clicks": 2500,
            "average_ctr": 0.05,
            "revenue_by_platform": {
                "desktop": 750.30,
                "mobile": 500.20
            },
            "revenue_by_country": {
                "US": 800.40,
                "UK": 450.10
            }
        }

    Raises:
        404: Publisher not found or doesn't belong to current user
    """
    publisher = await Publisher.get_user_publisher(
        session, current_user.id, publisher_id
    )
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return await publisher.get_stats(session)


@publisher_router.get("/{publisher_id}/revenue", response_model=RevenueStats)
async def get_publisher_revenue(
    publisher_id: str,
    start_date: datetime | None = Query(
        None, description="Start date for filtering statistics (format: YYYY-MM-DD)"
    ),
    end_date: datetime | None = Query(
        None, description="End date for filtering statistics (format: YYYY-MM-DD)"
    ),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get detailed revenue statistics for a publisher. Only returns stats for publishers owned by the current user.

    Examples:
        # Get all-time revenue stats
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k/revenue

        # Get revenue stats for a specific date range
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k/revenue?start_date=2024-01-01&end_date=2024-01-31

    Returns:
        {
            "publisher_id": "clh2x3e0h0000qw9k3q7q8j9k",
            "total_revenue": 1250.50,
            "publisher_share": 812.83,
            "platform_share": 437.67,
            "interaction_totals": {
                "impressions": 50000,
                "clicks": 2500,
                "views": 1500
            },
            "revenue_by_interaction": {
                "impression": 250.10,
                "click": 750.30,
                "view": 250.10
            },
            "revenue_by_country": {
                "US": 800.40,
                "UK": 450.10
            },
            "revenue_by_device": {
                "desktop": 750.30,
                "mobile": 500.20
            },
            "daily_revenue_trend": [
                {"date": "2024-01-01", "revenue": 42.50},
                {"date": "2024-01-02", "revenue": 38.75}
            ],
            "minimum_payout": 100.00,
            "payment_schedule": "monthly",
            "stats_period": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        }

    Raises:
        404: Publisher not found or doesn't belong to current user
    """
    # Get publisher
    publisher = await Publisher.get_user_publisher(
        session, current_user.id, publisher_id
    )
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")

    # Get revenue statistics
    revenue_service = RevenueService()
    stats = await revenue_service.get_publisher_revenue_stats(
        session,
        publisher,
        start_date=start_date,
        end_date=end_date,
    )

    return stats


@publisher_router.get(
    "/{publisher_id}/periodic-revenue",
    response_model=PeriodicRevenue,
    summary="Get periodic revenue breakdown",
    description="Get detailed revenue breakdown for a specific period, including interaction stats",
)
async def get_periodic_revenue(
    publisher_id: str,
    start_date: datetime = Query(
        default=None,
        description="Start date for the period (default: start of current day)",
    ),
    end_date: datetime = Query(
        default=None,
        description="End date for the period (default: end of current day)",
    ),
    period: str = Query(
        default="daily",
        description="Period type (daily or weekly)",
        regex="^(daily|weekly)$",
    ),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PeriodicRevenue:
    """Get periodic revenue breakdown for a publisher. Only returns stats for publishers owned by the current user.

    Examples:
        # Get today's revenue breakdown
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k/periodic-revenue

        # Get this week's revenue breakdown
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k/periodic-revenue?period=weekly

        # Get revenue breakdown for a custom period
        GET /api/v1/publishers/clh2x3e0h0000qw9k3q7q8j9k/periodic-revenue?start_date=2024-01-01T00:00:00Z&end_date=2024-01-07T00:00:00Z

    Returns:
        {
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-01-07T00:00:00Z",
            "total_revenue": 875.50,
            "publisher_share": 569.08,
            "impressions": {
                "count": 35000,
                "revenue": 175.10,
                "share": 113.82
            },
            "clicks": {
                "count": 1750,
                "revenue": 525.30,
                "share": 341.45
            },
            "views": {
                "count": 1050,
                "revenue": 175.10,
                "share": 113.82
            },
            "revenue_by_country": {
                "US": 560.30,
                "UK": 315.20
            },
            "revenue_by_device": {
                "desktop": 525.30,
                "mobile": 350.20
            }
        }

    Raises:
        404: Publisher not found or doesn't belong to current user
    """
    # Check publisher ownership
    publisher = await Publisher.get_user_publisher(
        session, current_user.id, publisher_id
    )
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")

    # Set default dates if not provided
    now = datetime.now(UTC)
    if period == "weekly":
        if not start_date:
            # Start from beginning of current week (Monday)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = start_date + timedelta(days=7)
    else:  # daily
        if not start_date:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = start_date + timedelta(days=1)

    # Get revenue stats
    stats = await PublisherEarnings.get_periodic_revenue(
        session, publisher_id, start_date, end_date
    )

    return PeriodicRevenue(**stats)
