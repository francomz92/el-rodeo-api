from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities._subscription import Subscription
from src.common.domain.repository import IRepository


class ISubscriptionRepository(IRepository):
    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription:
        """Persist a new subscription."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, subscription: Subscription) -> Subscription:
        """Update an existing subscription."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID) -> Subscription | None:
        """Retrieve the current subscription for a tenant, or None."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Subscription | None:
        """Retrieve a subscription by its UUID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def list_expired_trials(self) -> list[Subscription]:
        """Return all subscriptions whose trial has ended but are still active."""
        raise NotImplementedError

    @abstractmethod
    async def list_active_near_period_end(self, days_ahead: int) -> list[Subscription]:
        """Return ACTIVE subscriptions whose current_period_end is within the
        given number of days from now (and still in the future).

        This is used by the Celery monthly billing task to proactively create
        payment preferences before the current period ends.
        """
        raise NotImplementedError
