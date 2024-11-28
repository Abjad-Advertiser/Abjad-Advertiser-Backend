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
    ) -> "BillingData" | None:
        """Get billing data for a user

        Args:
            db_session: The database session
            user_id: ID of the user to get billing for

        Returns:
            BillingData object if found, None otherwise
        """
        result = await db_session.execute(select(cls).where(cls.user_id == user_id))
        return result.scalars().first()

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
        existing = await cls.get_billing(db_session, user_id)
        if existing:
            raise HTTPException(
                status_code=400, detail="Billing data already exists for this user"
            )

        billing_data = cls(
            user_id=user_id,
            billing_address=data.billing_address,
            tax_id=data.tax_id,
            currency=data.currency,
        )
        db_session.add(billing_data)
        await db_session.commit()
        await db_session.refresh(billing_data)
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
        if data.billing_address is not None:
            self.billing_address = data.billing_address
        if data.tax_id is not None:
            self.tax_id = data.tax_id
        if data.currency is not None:
            self.currency = data.currency

        await db_session.commit()
        await db_session.refresh(self)
        return self


# ================= FastAPI Dependencies =================


async def get_user_billing(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> BillingData:
    billing_data = await BillingData.get_billing(
        db_session=session, user_id=current_user.id
    )
    if not billing_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User billing data not found",
        )
    return billing_data
