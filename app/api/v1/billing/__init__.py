from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.dependencies.fast_api_users import current_active_user
from app.models.billing_datas import BillingData
from app.models.users import User
from app.schemas.billing import (BillingDataCreate, BillingDataResponse,
                                 BillingDataUpdate)

billing_router = APIRouter(prefix="/billing", tags=["billing"])


@billing_router.post("/", response_model=BillingDataResponse)
async def create_billing_data(
    data: BillingDataCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create billing data for the current user"""
    return await BillingData.create_billing(session, current_user.id, data)


@billing_router.get("/", response_model=BillingDataResponse)
async def get_billing_data(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get billing data for the current user"""
    billing_data = await BillingData.get_billing(session, current_user.id)
    if not billing_data:
        raise HTTPException(status_code=404, detail="Billing data not found")
    return billing_data


@billing_router.put("/", response_model=BillingDataResponse)
async def update_billing_data(
    data: BillingDataUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update billing data for the current user"""
    billing_data = await BillingData.get_billing(session, current_user.id)
    if not billing_data:
        raise HTTPException(status_code=404, detail="Billing data not found")
    return await billing_data.update_billing(session, data)
