import logging

from fastapi import Depends, HTTPException
from sqlalchemy import Column, Float, ForeignKey, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_async_session
from app.db.db_session import Base
from app.dependencies.fast_api_users import current_active_user
from app.models.users import User
from app.schemas.billing import BillingDataCreate, BillingDataUpdate
from app.utils.cuid import generate_cuid

logger = logging.getLogger(__name__)


class BillingData(Base):
    __tablename__ = "billing_datas"

    id: str = Column(String, primary_key=True, default=generate_cuid, nullable=False)
    user_id: str = Column(String, ForeignKey("users.id"), unique=True, index=True)

    billing_address = Column(String(200))
    tax_id = Column(String(20))
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    @classmethod
    async def get_billing(
        cls: "BillingData", db_session: AsyncSession, user_id: str
    ) -> "BillingData":
        """Get billing data for a user

        Args:
            db_session: The database session
            user_id: ID of the user to get billing for

        Returns:
            BillingData object if found, None otherwise
        """
        logger.info(f"Fetching billing data for user: {user_id}")
        result = await db_session.execute(select(cls).where(cls.user_id == user_id))
        billing_data = result.scalars().first()
        if billing_data:
            logger.info(f"Billing data found for user: {user_id}")
        else:
            logger.info(f"No billing data found for user: {user_id}")
        return billing_data

    @classmethod
    async def create_billing(
        cls: "BillingData",
        db_session: AsyncSession,
        user_id: str,
        data: BillingDataCreate,
    ) -> "BillingData":
        """Create billing data for a user

        Args:
            db_session: The database session
            user_id: ID of the user to create billing for
            data: Billing data to create

        Returns:
            Created BillingData object

        Raises:
            HTTPException: If billing data already exists for user
        """
        logger.info(f"Attempting to create billing data for user: {user_id}")
        existing = await cls.get_billing(db_session, user_id)
        if existing:
            logger.warning(f"Billing data already exists for user: {user_id}")
            raise HTTPException(
                status_code=400, detail="Billing data already exists for this user"
            )

        if data.currency not in ["USD"]:
            logger.error(
                f"Invalid currency {
                    data.currency} for user: {user_id}"
            )
            raise HTTPException(status_code=400, detail="Currency must be 'USD'")

        billing_data = cls(
            user_id=user_id,
            billing_address=data.billing_address,
            tax_id=data.tax_id,
            currency=data.currency,
        )
        db_session.add(billing_data)
        await db_session.commit()
        await db_session.refresh(billing_data)
        logger.info(f"Billing data created successfully for user: {user_id}")
        return billing_data

    async def update_billing(
        self, db_session: AsyncSession, data: BillingDataUpdate
    ) -> "BillingData":
        """Update billing data

        Args:
            db_session: The database session
            data: Updated billing data

        Returns:
            Updated BillingData object
        """
        logger.info(f"Updating billing data for user: {self.user_id}")
        if data.billing_address is not None:
            self.billing_address = data.billing_address
        if data.tax_id is not None:
            self.tax_id = data.tax_id
        if data.currency is not None:
            self.currency = data.currency

        await db_session.commit()
        await db_session.refresh(self)
        logger.info(
            f"Billing data updated successfully for user: {
                self.user_id}"
        )
        return self


# ================= FastAPI Dependencies =================


async def get_user_billing(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> BillingData:
    logger.info(f"Fetching billing data for current user: {current_user.id}")
    billing_data = await BillingData.get_billing(
        db_session=session, user_id=current_user.id
    )
    if not billing_data:
        logger.warning(f"Billing data not found for user: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User billing data not found",
        )
    return billing_data
