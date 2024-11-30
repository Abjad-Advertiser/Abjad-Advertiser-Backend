import enum

import money
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.billing_datas import BillingData
from app.utils.cuid import generate_cuid

from .exceptions import ModelError


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String, autoincrement=False, primary_key=True, default=generate_cuid)

    campaign_name = Column(String, nullable=False)
    campaign_description = Column(String, nullable=False)
    campaign_start_date = Column(DateTime, nullable=False)
    campaign_end_date = Column(DateTime, nullable=False)

    campaign_status = Column(
        Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT
    )
    campaign_budget = Column(String, nullable=True, default="0.00_USD")
    campaign_budget_used = Column(String, nullable=True, default="0.00_USD")

    advertisement_id = Column(String, ForeignKey("advertisements.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    publisher_id = Column(String, ForeignKey("publishers.id"), nullable=True)

    publisher = relationship("Publisher", back_populates="campaigns")

    def __iter__(self):
        """Make the model iterable to support dict() conversion."""
        yield "id", self.id
        yield "campaign_name", self.campaign_name
        yield "campaign_description", self.campaign_description
        yield "campaign_start_date", self.campaign_start_date
        yield "campaign_end_date", self.campaign_end_date
        yield "campaign_status", self.campaign_status
        yield "campaign_budget", self.campaign_budget
        yield "advertisement_id", self.advertisement_id
        yield "user_id", self.user_id
        yield "publisher_id", self.publisher_id

    @classmethod
    async def create_campaign(
        cls: "Campaign",
        session: AsyncSession,
        campaign_data: dict,
        billing_data: BillingData,
        user_id: str,
    ) -> "Campaign":
        """Create a new campaign with budget allocation.

        Args:
            session: The database session
            campaign_data: Dictionary containing campaign creation data including budget information
            billing_data: User's billing data for budget validation
            user_id: ID of the user creating the campaign

        Raises:
            ModelError: If budget allocation exceeds available balance

        Returns:
            Campaign: The created campaign
        """
        # Validate and process budge
        allocated_budget = money.Money(
            campaign_data["budget_allocation_amount"],
            campaign_data["budget_allocation_currency"],
        )

        # Convert budget to USD if needed
        if allocated_budget.currency != "USD":
            allocated_budget = allocated_budget.to("USD")

        # Calculate total budget for all campaigns including the new one
        # NOTE: Lazy approuch, but works for now.
        # TODO: Find a better solution
        all_campaigns = await cls.get_user_campaigns(session, user_id)
        total_budget = sum(
            float(c.campaign_budget.split("_")[0]) for c in all_campaigns
        )
        total_budget += float(allocated_budget.amount)

        # Check if total budget exceeds available balance
        if total_budget > billing_data.balance:
            raise ModelError(
                reason="Insufficient balance for all campaigns", status=400
            )

        # Update campaign_budget to use USD
        campaign_data["campaign_budget"] = f"{
            allocated_budget.amount:.2f}_{
            billing_data.currency}"

        campaign = cls(
            campaign_name=campaign_data["campaign_name"],
            campaign_description=campaign_data["campaign_description"],
            campaign_start_date=campaign_data["campaign_start_date"],
            campaign_end_date=campaign_data["campaign_end_date"],
            campaign_status=CampaignStatus.DRAFT,
            campaign_budget=str(allocated_budget),
            advertisement_id=campaign_data["advertisement_id"],
            user_id=user_id,
        )

        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        return campaign

    @classmethod
    async def get_user_campaigns(
        cls: "Campaign", session: AsyncSession, user_id: str
    ) -> list["Campaign"]:
        """Get all campaigns for a specific user.

        Args:
            session: The database session
            user_id: ID of the user

        Returns:
            List[Campaign]: List of campaigns belonging to the user
        """
        result = await session.execute(
            cls.__table__.select().where(cls.user_id == user_id)
        )
        return result.all()

    @classmethod
    async def get_campaign_by_id(
        cls: "Campaign", session: AsyncSession, campaign_id: str, user_id: str
    ) -> dict:
        """Get a specific campaign by ID.

        Args:
            session: The database session
            campaign_id: ID of the campaign
            user_id: ID of the user

        Raises:
            ModelError: If campaign not found

        Returns:
            dict: The requested campaign
        """
        result = await session.execute(
            cls.__table__.select().where(cls.id == campaign_id, cls.user_id == user_id)
        )
        row = result.first()

        if not row:
            raise ModelError(status=404, reason="Campaign not found")

        # Convert row to dict using column names
        return {c.name: getattr(row, c.name) for c in cls.__table__.columns}

    @classmethod
    async def update_campaign_status(
        cls: "Campaign",
        session: AsyncSession,
        campaign_id: str,
        user_id: str,
        new_status: CampaignStatus,
    ) -> None:
        """Update campaign status.

        Args:
            session: The database session
            campaign_id: ID of the campaign
            user_id: ID of the user
            new_status: New campaign status

        Raises:
            ModelError: If campaign not found
        """
        # First check if campaign exists
        await cls.get_campaign_by_id(session, campaign_id, user_id)

        await session.execute(
            cls.__table__.update()
            .where(cls.id == campaign_id)
            .values(campaign_status=new_status)
        )
        await session.commit()

    @classmethod
    async def delete_campaign(
        cls: "Campaign", session: AsyncSession, campaign_id: str, user_id: str
    ) -> None:
        """Delete a campaign.

        Args:
            session: The database session
            campaign_id: ID of the campaign
            user_id: ID of the user

        Raises:
            ModelError: If campaign not found
        """
        # First check if campaign exists
        await cls.get_campaign_by_id(session, campaign_id, user_id)

        await session.execute(cls.__table__.delete().where(cls.id == campaign_id))
        await session.commit()

    async def increase_budget_used(self, session: AsyncSession, amount: float) -> None:
        """
        Increase the amount of budget used for this campaign.

        Args:
            session: The database session
            amount: The amount to increase (must be positive)

        Raises:
            ModelError: If the budget would be exceeded or amount is invalid
        """
        if amount <= 0:
            raise ModelError(reason="Amount must be positive", status=400)

        # Parse current budget and used amount
        current_budget = float(self.campaign_budget.split("_")[0])
        current_used = float(self.campaign_budget_used.split("_")[0])
        currency = self.campaign_budget.split("_")[1]

        # Check if increasing would exceed budget
        if current_used + amount > current_budget:
            raise ModelError(
                reason=f"Budget would be exceeded. Available: {
                    current_budget -
                    current_used} {currency}",
                status=400,
            )

        # Update the used amount
        self.campaign_budget_used = f"{current_used + amount:.2f}_{currency}"
        await session.commit()
