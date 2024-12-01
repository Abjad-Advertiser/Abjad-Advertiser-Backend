from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger as logging
from app.db.db_session import Base
from app.utils.cuid import generate_cuid
from app.utils.pricing import PricingManager

# deferred imports to prevent circular imports
if TYPE_CHECKING:
    pass


class WithdrawalStatus(str, Enum):
    """Status of publisher earnings withdrawal."""

    PENDING = "pending"  # Initial state
    WITHDRAWAL_REQUESTED = "withdrawal_requested"  # Publisher requested withdrawal
    WITHDRAWAL_APPROVED = "withdrawal_approved"  # Admin approved withdrawal
    WITHDRAWAL_COMPLETED = "withdrawal_completed"  # Payment sent to publisher
    WITHDRAWAL_REJECTED = "withdrawal_rejected"  # Admin rejected withdrawal


class PublisherEarnings(Base):
    __tablename__ = "publisher_earnings"

    id = Column(String, primary_key=True, autoincrement=False, default=generate_cuid)
    publisher_id = Column(String, ForeignKey("publishers.id"), nullable=False)

    month = Column(DateTime(timezone=True), nullable=False)  # First day of the month

    total_views = Column(Integer, default=0, nullable=False)
    total_clicks = Column(Integer, default=0, nullable=False)
    total_impressions = Column(Integer, default=0, nullable=False)

    gross_revenue = Column(Float, default=0.0, nullable=False)
    publisher_share = Column(Float, default=0.0, nullable=False)  # 65% of gross revenue
    platform_share = Column(Float, default=0.0, nullable=False)  # 35% of gross revenue

    withdrawal_status = Column(
        SQLEnum(WithdrawalStatus), default=WithdrawalStatus.PENDING
    )
    withdrawal_requested_at = Column(DateTime(timezone=True), nullable=True)
    withdrawal_processed_at = Column(DateTime(timezone=True), nullable=True)
    withdrawal_notes = Column(String, nullable=True)

    is_paid = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    paid_at = Column(DateTime(timezone=True), nullable=True)

    @classmethod
    async def get_monthly_earnings(
        cls, db_session: AsyncSession, publisher_id: str, month: datetime
    ) -> "PublisherEarnings":
        """Get earnings for a specific month"""
        result = await db_session.execute(
            select(cls).where(
                and_(
                    cls.publisher_id == publisher_id,
                    # First day of the month
                    cls.month == month.replace(day=1),
                )
            )
        )
        return result.scalars().first()

    @classmethod
    async def create_or_update_earnings(
        cls,
        db_session: AsyncSession,
        publisher_id: str,
        month: datetime,
        views: int = 0,
        clicks: int = 0,
        impressions: int = 0,
        gross_revenue: float = 0.0,
        publisher_share: float = 0.0,
        platform_share: float = 0.0,
    ) -> "PublisherEarnings":
        """Create or update earnings for a month"""
        logging.info(f"Creating or updating earnings for publisher {
                     publisher_id} for month {month.strftime('%Y-%m')}")
        earnings = await cls.get_monthly_earnings(db_session, publisher_id, month)
        if not earnings:
            logging.info(f"Creating new earnings record for publisher {
                         publisher_id} for month {month.strftime('%Y-%m')}")
            earnings = cls(
                publisher_id=publisher_id,
                month=month.replace(day=1),
                total_views=0,
                total_clicks=0,
                total_impressions=0,
                gross_revenue=0.0,
                publisher_share=0.0,
                platform_share=0.0,
            )
            db_session.add(earnings)
        else:
            logging.info(f"Updating existing earnings for publisher {
                         publisher_id} for month {month.strftime('%Y-%m')}")

        logging.info(
            f"Current earnings state - Gross: ${
                earnings.gross_revenue or 0:.4f}, Publisher: ${
                earnings.publisher_share or 0:.4f}, Platform: ${
                earnings.platform_share or 0:.4f}"
        )

        # Update stats with null checks
        earnings.total_views = (earnings.total_views or 0) + views
        earnings.total_clicks = (earnings.total_clicks or 0) + clicks
        earnings.total_impressions = (earnings.total_impressions or 0) + impressions

        if views:
            logging.info(
                f"Incrementing views by {views}, new total: {
                    earnings.total_views}"
            )
        if clicks:
            logging.info(
                f"Incrementing clicks by {clicks}, new total: {
                    earnings.total_clicks}"
            )
        if impressions:
            logging.info(
                f"Incrementing impressions by {impressions}, new total: {
                    earnings.total_impressions}"
            )

        # Update earnings
        earnings.gross_revenue = (earnings.gross_revenue or 0.0) + gross_revenue
        earnings.publisher_share = (earnings.publisher_share or 0.0) + publisher_share
        earnings.platform_share = (earnings.platform_share or 0.0) + platform_share

        logging.info(
            f"Updated earnings state - Gross: ${
                earnings.gross_revenue:.4f}, Publisher: ${
                earnings.publisher_share:.4f}, Platform: ${
                earnings.platform_share:.4f}"
        )

        await db_session.commit()
        return earnings

    @classmethod
    async def get_revenue_stats(
        cls,
        session: AsyncSession,
        publisher_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """Get comprehensive revenue statistics for a publisher.

        Args:
            session: Database session
            publisher_id: ID of the publisher
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dict containing revenue statistics
        """
        # Get monthly earnings for the period
        query = select(cls).where(cls.publisher_id == publisher_id)
        if start_date:
            query = query.where(cls.month >= start_date.replace(day=1))
        if end_date:
            query = query.where(cls.month <= end_date.replace(day=1))

        result = await session.execute(query)
        earnings_records = result.scalars().all()

        # Calculate totals from monthly records
        total_revenue = sum(e.gross_revenue for e in earnings_records)
        total_publisher_share = sum(e.publisher_share for e in earnings_records)
        total_platform_share = sum(e.platform_share for e in earnings_records)
        total_views = sum(e.total_views for e in earnings_records)
        total_clicks = sum(e.total_clicks for e in earnings_records)
        total_impressions = sum(e.total_impressions for e in earnings_records)

        # Get detailed breakdowns from tracking events
        interaction_stats = await cls.get_interaction_stats(
            session, publisher_id, start_date, end_date
        )

        # Get daily revenue trend
        daily_trend = await cls.get_daily_revenue_trend(session, publisher_id)

        return {
            "total_revenue": total_revenue,
            "publisher_share": total_publisher_share,
            "platform_share": total_platform_share,
            "interaction_totals": {
                "views": total_views,
                "clicks": total_clicks,
                "impressions": total_impressions,
            },
            "revenue_by_interaction": interaction_stats["revenue_by_interaction"],
            "revenue_by_country": interaction_stats["revenue_by_country"],
            "revenue_by_device": interaction_stats["revenue_by_device"],
            "daily_revenue_trend": daily_trend,
            "stats_period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        }

    @classmethod
    async def get_interaction_stats(
        cls,
        session: AsyncSession,
        publisher_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """Get detailed interaction statistics from tracking events.

        Args:
            session: Database session
            publisher_id: ID of the publisher
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dict containing interaction statistics
        """
        from app.models.tracking_events import TrackingEvent

        # Query tracking events
        query = select(TrackingEvent).where(TrackingEvent.publisher_id == publisher_id)
        if start_date:
            query = query.where(TrackingEvent.event_timestamp >= start_date)
        if end_date:
            query = query.where(TrackingEvent.event_timestamp <= end_date)

        result = await session.execute(query)
        events = result.scalars().all()

        # Initialize statistics containers
        revenue_by_interaction = {"impression": 0.0, "click": 0.0, "view": 0.0}
        revenue_by_country = {}
        revenue_by_device = {"mobile": 0.0, "tablet": 0.0, "desktop": 0.0}

        # Calculate breakdowns
        for event in events:
            revenue = event.publisher_earnings

            # By interaction type
            revenue_by_interaction[event.event_type.value] += revenue

            # By country
            if event.viewer_country not in revenue_by_country:
                revenue_by_country[event.viewer_country] = 0.0
            revenue_by_country[event.viewer_country] += revenue

            # By device type
            device_type = event.viewer_device_type.lower()
            if device_type in revenue_by_device:
                revenue_by_device[device_type] += revenue

        return {
            "revenue_by_interaction": revenue_by_interaction,
            "revenue_by_country": revenue_by_country,
            "revenue_by_device": revenue_by_device,
        }

    @classmethod
    async def get_daily_revenue_trend(
        cls, session: AsyncSession, publisher_id: str, days: int = 30
    ) -> list[dict[str, float]]:
        """Get daily revenue trend for the past N days."""
        from app.models.tracking_events import TrackingEvent

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        # Query daily revenue
        query = (
            select(
                func.date_trunc("day", TrackingEvent.event_timestamp).label("date"),
                func.sum(TrackingEvent.earnings).label("revenue"),
            )
            .where(
                and_(
                    TrackingEvent.publisher_id == publisher_id,
                    TrackingEvent.event_timestamp >= start_date,
                    TrackingEvent.event_timestamp <= end_date,
                )
            )
            .group_by(func.date_trunc("day", TrackingEvent.event_timestamp))
            .order_by(func.date_trunc("day", TrackingEvent.event_timestamp))
        )

        result = await session.execute(query)
        return [
            {"date": row.date.strftime("%Y-%m-%d"), "revenue": float(row.revenue)}
            for row in result
        ]

    @classmethod
    async def get_periodic_revenue(
        cls,
        session: AsyncSession,
        publisher_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Get detailed revenue breakdown for a specific period."""
        from app.models.tracking_events import TrackingEvent

        # Get tracking events for the period
        query = select(TrackingEvent).where(
            and_(
                TrackingEvent.publisher_id == publisher_id,
                TrackingEvent.event_timestamp >= start_date,
                TrackingEvent.event_timestamp <= end_date,
            )
        )
        result = await session.execute(query)
        tracking_events = result.scalars().all()

        # Initialize revenue stats
        stats = {
            "period_start": start_date,
            "period_end": end_date,
            "total_revenue": 0.0,
            "publisher_share": 0.0,
            "impressions": {"count": 0, "revenue": 0.0, "share": 0.0},
            "clicks": {"count": 0, "revenue": 0.0, "share": 0.0},
            "views": {"count": 0, "revenue": 0.0, "share": 0.0},
            "revenue_by_country": {},
            "revenue_by_device": {},
        }

        # Process events
        for event in tracking_events:
            event_revenue = event.earnings
            event_share = event.publisher_earnings

            # Update total revenue
            stats["total_revenue"] += event_revenue
            stats["publisher_share"] += event_share

            # Update interaction stats
            interaction_type = event.event_type.value
            if interaction_type in ["impression", "click", "view"]:
                key = interaction_type + "s"  # pluralize
                stats[key]["count"] += 1
                stats[key]["revenue"] += event_revenue
                stats[key]["share"] += event_share

            # Update country stats
            country = event.viewer_country or "unknown"
            stats["revenue_by_country"][country] = (
                stats["revenue_by_country"].get(country, 0) + event_revenue
            )

            # Update device stats
            device = event.viewer_device_type or "unknown"
            stats["revenue_by_device"][device] = (
                stats["revenue_by_device"].get(device, 0) + event_revenue
            )

        return stats

    @classmethod
    async def request_withdrawal(
        cls,
        db_session: AsyncSession,
        publisher_id: str,
        month: datetime,
    ) -> tuple[bool, str]:
        """Request withdrawal of earnings for a specific month.

        Returns:
            Tuple of (success, message)
        """
        # Get earnings record
        earnings = await cls.get_monthly_earnings(db_session, publisher_id, month)
        if not earnings:
            return False, "No earnings found for the specified month"

        # Check if withdrawal is already in progress
        if earnings.withdrawal_status != WithdrawalStatus.PENDING:
            return (
                False,
                f"Withdrawal already in {
                    earnings.withdrawal_status} status",
            )

        # Check minimum days passed (7 days)
        min_days = 7
        days_passed = (datetime.now(UTC) - earnings.created_at).days
        if days_passed < min_days:
            return (
                False,
                f"Must wait {
                    min_days -
                    days_passed} more days before requesting withdrawal",
            )

        # Check minimum payout amount
        min_payout = PricingManager().minimum_payout
        if earnings.publisher_share < min_payout:
            return False, f"Minimum payout amount is ${min_payout:.2f}"

        # Update status
        earnings.withdrawal_status = WithdrawalStatus.WITHDRAWAL_REQUESTED
        earnings.withdrawal_requested_at = datetime.now(UTC)
        await db_session.commit()

        return True, "Withdrawal request submitted successfully"

    @classmethod
    async def process_withdrawal(
        cls,
        db_session: AsyncSession,
        earnings_id: str,
        approve: bool,
        notes: str | None = None,
    ) -> tuple[bool, str]:
        """Process (approve/reject) a withdrawal request.

        Args:
            db_session: Database session
            earnings_id: ID of the earnings record
            approve: True to approve, False to reject
            notes: Optional notes about the decision

        Returns:
            Tuple of (success, message)
        """
        # Get earnings record
        result = await db_session.execute(select(cls).where(cls.id == earnings_id))
        earnings = result.scalar_one_or_none()
        if not earnings:
            return False, "Earnings record not found"

        # Check if request is pending
        if earnings.withdrawal_status != WithdrawalStatus.WITHDRAWAL_REQUESTED:
            return (
                False,
                f"Cannot process withdrawal in {
                    earnings.withdrawal_status} status",
            )

        # Update status
        if approve:
            earnings.withdrawal_status = WithdrawalStatus.WITHDRAWAL_COMPLETED
        else:
            earnings.withdrawal_status = WithdrawalStatus.WITHDRAWAL_REJECTED

        earnings.withdrawal_processed_at = datetime.now(UTC)
        earnings.withdrawal_notes = notes

        await db_session.commit()

        status = "approved" if approve else "rejected"
        return True, f"Withdrawal request {status} successfully"

    @classmethod
    async def get_pending_withdrawals(
        cls,
        db_session: AsyncSession,
    ) -> list["PublisherEarnings"]:
        """Get all pending withdrawal requests."""
        result = await db_session.execute(
            select(cls)
            .where(cls.withdrawal_status == WithdrawalStatus.WITHDRAWAL_REQUESTED)
            .order_by(cls.withdrawal_requested_at)
        )
        return result.scalars().all()
