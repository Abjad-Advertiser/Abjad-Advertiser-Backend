"""Publisher API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.dependencies.fast_api_users import current_active_user
from app.models.publisher import Publisher
from app.models.users import User
from app.schemas.publisher import (PublisherCreate, PublisherResponse,
                                   PublisherStats, PublisherUpdate)

publisher_router = APIRouter(prefix="/publishers", tags=["publishers"])


@publisher_router.post("/", response_model=PublisherResponse)
async def create_publisher(
    data: PublisherCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Publisher:
    """Create a new publisher."""
    return await Publisher.create(session, data)


@publisher_router.get("/", response_model=list[PublisherResponse])
async def list_publishers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[Publisher]:
    """Get all publishers with pagination."""
    return await Publisher.get_all(session, skip=skip, limit=limit)


@publisher_router.get("/{publisher_id}", response_model=PublisherResponse)
async def get_publisher(
    publisher_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Publisher:
    """Get a specific publisher by ID."""
    publisher = await Publisher.get(session, publisher_id)
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
    """Update a publisher's details."""
    publisher = await Publisher.get(session, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return await publisher.update(session, data)


@publisher_router.delete("/{publisher_id}")
async def delete_publisher(
    publisher_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete a publisher."""
    publisher = await Publisher.get(session, publisher_id)
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
    """Get statistics for a specific publisher."""
    publisher = await Publisher.get(session, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return await publisher.get_stats(session)
