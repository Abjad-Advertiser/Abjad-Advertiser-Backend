from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.dependencies.fast_api_users import current_active_user
from app.models.advertisements import Advertisement
from app.models.exceptions import ModelError
from app.models.users import User
from app.schemas.advertisements import (AdvertisementCreate,
                                        AdvertisementResponse,
                                        AdvertisementUpdate)

advertisers_router = APIRouter(prefix="/advertisers", tags=["Advertisers"])


@advertisers_router.post(
    "/create-ad",
    response_model=AdvertisementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ad(
    ad_data: AdvertisementCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new advertisement"""
    try:
        ad = await Advertisement.create_ad(session, ad_data, user.id)
        return ad
    except ModelError as e:
        raise HTTPException(status_code=400, detail=str(e))


@advertisers_router.get("/ad", response_model=list[AdvertisementResponse])
async def get_user_ads(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all advertisements for the current user"""
    ads = await Advertisement.get_user_ads(session, user.id)
    return ads


@advertisers_router.get("/ad/{ad_id}", response_model=AdvertisementResponse)
async def get_ad(
    ad_id: str = Path(..., description="The ID of the advertisement to get"),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get a specific advertisement"""
    ad = await Advertisement.get_ad(session, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    if ad.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this advertisement"
        )
    return ad


@advertisers_router.put("/ad/{ad_id}", response_model=AdvertisementResponse)
async def update_ad(
    ad_data: AdvertisementUpdate,
    ad_id: str = Path(..., description="The ID of the advertisement to update"),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update an advertisement"""
    ad = await Advertisement.get_ad(session, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    if ad.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this advertisement"
        )

    updated_ad = await ad.update_ad(session, ad_data)
    return updated_ad


@advertisers_router.delete("/ad/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(
    ad_id: str = Path(..., description="The ID of the advertisement to delete"),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete an advertisement"""
    ad = await Advertisement.get_ad(session, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    if ad.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this advertisement"
        )

    await ad.delete_ad(session)
