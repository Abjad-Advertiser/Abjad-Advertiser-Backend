"""Service for handling publisher revenue calculations and updates."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.publisher import Publisher
from app.models.publisher_earnings import PublisherEarnings
from app.models.tracking_events import TrackingEvent
from app.utils.pricing import PricingManager


class RevenueService:
    """Service for managing publisher revenue calculations and updates."""

    def __init__(self):
        """Initialize the revenue service."""
        self.pricing_manager = PricingManager()

    async def process_tracking_event(
        self,
        session: AsyncSession,
        event: TrackingEvent,
        publisher: Publisher,
    ) -> dict:
        """Process a tracking event and update publisher revenue.

        Args:
            session: Database session
            event: The tracking event to process
            publisher: The publisher to update revenue for

        Returns:
            Dict containing the revenue calculation details
        """
        # Update publisher's revenue
        await publisher.update_revenue(session, event.publisher_earnings)

        return {
            "event_id": event.id,
            "publisher_id": publisher.id,
            "timestamp": datetime.utcnow(),
            "earnings": event.earnings,
            "publisher_earnings": event.publisher_earnings,
            "platform_earnings": event.platform_earnings,
        }

    async def get_publisher_revenue_stats(
        self,
        session: AsyncSession,
        publisher: Publisher,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """Get revenue statistics for a publisher.

        Args:
            session: Database session
            publisher: The publisher to get stats for
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dict containing revenue statistics
        """
        stats = await PublisherEarnings.get_revenue_stats(
            session, publisher.id, start_date, end_date
        )

        # Add publisher-specific payment info
        stats.update(
            {
                "publisher_id": publisher.id,
                "currency": "USD",  # Using USD as default currency for now
                "minimum_payout": self.pricing_manager.minimum_payout,
                "payment_schedule": self.pricing_manager.payment_schedule,
            }
        )

        return stats
