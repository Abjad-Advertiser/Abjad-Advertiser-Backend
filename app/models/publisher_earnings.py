from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, and_, func, select)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_session import Base
from app.utils.cuid import generate_cuid

# deferred imports to prevent circular imports
if TYPE_CHECKING:
    pass


class PublisherEarnings(Base):
    __tablename__ = "publisher_earnings"

    id = Column(String, primary_key=True, default=generate_cuid)
    publisher_id = Column(String, ForeignKey("publishers.id"), nullable=False)
    month = Column(DateTime, nullable=False)  # First day of the month
    total_views = Column(Integer, default=0, nullable=False)
    total_clicks = Column(Integer, default=0, nullable=False)
    total_impressions = Column(Integer, default=0, nullable=False)
    gross_revenue = Column(Float, default=0.0, nullable=False)
    publisher_share = Column(Float, default=0.0, nullable=False)  # 65% of gross revenue
    platform_share = Column(Float, default=0.0, nullable=False)  # 35% of gross revenue
    is_paid = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    paid_at = Column(DateTime, nullable=True)

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
        revenue: float = 0.0,
    ) -> "PublisherEarnings":
        """Create or update earnings for a month"""
        earnings = await cls.get_monthly_earnings(db_session, publisher_id, month)

        if not earnings:
            earnings = cls(publisher_id=publisher_id, month=month.replace(day=1))
            db_session.add(earnings)

        # Update stats
        earnings.total_views += views
        earnings.total_clicks += clicks
        earnings.total_impressions += impressions
        earnings.gross_revenue += revenue

        # Calculate shares (35% platform, 65% publisher)
        earnings.platform_share = earnings.gross_revenue * 0.35
        earnings.publisher_share = earnings.gross_revenue * 0.65

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
