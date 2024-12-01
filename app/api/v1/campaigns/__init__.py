"""
Campaign Management API

This module defines the API endpoints for managing advertising campaigns.
It includes functionality for creating, retrieving, updating, and deleting campaigns.

Endpoints:
- POST /campaigns/: Create a new campaign
- GET /campaigns/: Retrieve all campaigns for the current user
- GET /campaigns/{campaign_id}: Retrieve a specific campaign by ID
- PATCH /campaigns/{campaign_id}/status: Update the status of a campaign
- DELETE /campaigns/{campaign_id}: Delete a specific campaign

The module uses FastAPI for routing and depends on SQLAlchemy for database operations.
It also utilizes custom models and schemas for data handling and validation.

Dependencies:
- FastAPI for API routing and request handling
- SQLAlchemy for asynchronous database operations
- Custom user authentication and authorization
- Campaign and User models for database interactions
- CampaignCreate schema for input validation

Error Handling:
- Raises HTTPException for various error scenarios, including bad requests and model errors

Note: This module assumes the existence of supporting modules and configurations,
such as database sessions, user authentication, and model definitions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db import get_async_session
from app.dependencies.fast_api_users import current_active_user
from app.models.billing_datas import BillingData, get_user_billing
from app.models.campaigns import Campaign, CampaignStatus
from app.models.exceptions import ModelError
from app.models.users import User
from app.schemas.campaigns import CampaignCreate

campaign_router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@campaign_router.post("/create-campaign", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    billing_data: BillingData = Depends(get_user_billing),
):
    """
    Create a new campaign for the authenticated user.

    This endpoint allows the creation of a new advertising campaign. It processes
    the input data, converts dates, formats the budget, and uses the Campaign model
    to create the campaign in the database.

    Args:
        campaign (CampaignCreate): The campaign data as validated by the CampaignCreate schema.
        current_user (User): The authenticated user creating the campaign.
        session (AsyncSession): The database session for executing the operation.
        billing_data (BillingData): The user's billing data.

    Returns:
        dict: The newly created campaign data.

    Raises:
        HTTPException:
            - 400 Bad Request if there's an error in date parsing or other validation.
            - Status code from ModelError if there's an error in campaign creation.
    """
    try:
        logger.info(f"Creating campaign for user: {current_user.id}")
        logger.info(f"Creating campaign: {campaign}")

        if campaign.budget_allocation_currency != billing_data.currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Budget currency must be the same as billing currency",
            )

        campaign_budget = f"{
            campaign.budget_allocation_amount}_{
            campaign.budget_allocation_currency}"
        campaign_data = {
            "campaign_name": campaign.name,
            "campaign_description": campaign.description,
            "campaign_start_date": campaign.campaign_start_date,
            "campaign_end_date": campaign.campaign_end_date,
            "campaign_budget": campaign_budget,
            "budget_allocation_amount": campaign.budget_allocation_amount,
            "budget_allocation_currency": campaign.budget_allocation_currency,
            "advertisement_id": campaign.advertisement_id,
        }

        new_campaign = await Campaign.create_campaign(
            session=session,
            campaign_data=campaign_data,
            billing_data=billing_data,
            user_id=current_user.id,
        )
        return new_campaign
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ModelError as e:
        raise HTTPException(status_code=e.status, detail=e.reason)


@campaign_router.get("/", response_model=list[dict])
async def get_campaigns(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieve all campaigns for the authenticated user.

    This endpoint fetches all campaigns associated with the current user from the database.

    Args:
        current_user (User): The authenticated user whose campaigns are being retrieved.
        session (AsyncSession): The database session for executing the query.

    Returns:
        list[dict]: A list of dictionaries, each representing a campaign.

    Raises:
        HTTPException: Status code from ModelError if there's an error retrieving campaigns.
    """
    try:
        campaigns = await Campaign.get_user_campaigns(
            session=session, user_id=current_user.id
        )
        return [dict(campaign) for campaign in campaigns]
    except ModelError as e:
        raise HTTPException(status_code=e.status, detail=e.reason)


@campaign_router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieve a specific campaign by its ID for the authenticated user.

    This endpoint fetches a single campaign with the given ID, ensuring it belongs to the current user.

    Args:
        campaign_id (str): The unique identifier of the campaign to retrieve.
        current_user (User): The authenticated user requesting the campaign.
        session (AsyncSession): The database session for executing the query.

    Returns:
        dict: A dictionary representing the requested campaign.

    Raises:
        HTTPException: Status code from ModelError if the campaign is not found or there's an error.
    """
    try:
        campaign = await Campaign.get_campaign_by_id(
            session=session, campaign_id=campaign_id, user_id=current_user.id
        )
        return campaign
    except ModelError as e:
        raise HTTPException(status_code=e.status, detail=e.reason)


@campaign_router.patch("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status_update: dict,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update the status of a specific campaign.

    This endpoint allows changing the status of a campaign identified by its ID.
    Only the owner of the campaign can perform this action.

    Args:
        campaign_id (str): The unique identifier of the campaign to update.
        status_update (dict): A dictionary containing the new_status field.
        current_user (User): The authenticated user requesting the update.
        session (AsyncSession): The database session for executing the update.

    Returns:
        dict: A message confirming the successful update of the campaign status.

    Raises:
        HTTPException: Status code from ModelError if there's an error updating the status.
    """
    try:
        if "new_status" not in status_update:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="new_status field is required in request body",
            )

        new_status = CampaignStatus(status_update["new_status"])
        await Campaign.update_campaign_status(
            session=session,
            campaign_id=campaign_id,
            user_id=current_user.id,
            new_status=new_status,
        )
        return {"message": "Campaign status updated successfully"}
    except ModelError as e:
        raise HTTPException(status_code=e.status, detail=e.reason)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {[s.value for s in CampaignStatus]}",
        )


@campaign_router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete a specific campaign.

    This endpoint allows the deletion of a campaign identified by its ID.
    Only the owner of the campaign can perform this action.

    Args:
        campaign_id (str): The unique identifier of the campaign to delete.
        current_user (User): The authenticated user requesting the deletion.
        session (AsyncSession): The database session for executing the deletion.

    Returns:
        dict: A message confirming the successful deletion of the campaign.

    Raises:
        HTTPException: Status code from ModelError if there's an error deleting the campaign.
    """
    try:
        await Campaign.delete_campaign(
            session=session, campaign_id=campaign_id, user_id=current_user.id
        )
        return {"message": "Campaign deleted successfully"}
    except ModelError as e:
        raise HTTPException(status_code=e.status, detail=e.reason)
