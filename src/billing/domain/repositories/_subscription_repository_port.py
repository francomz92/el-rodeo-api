from abc import abstractmethod
from uuid import UUID

from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.common.domain.repository import IRepository


class ISubscriptionRepository(IRepository):
    @abstractmethod
    async def create(self, subscription: SubscriptionEntity) -> SubscriptionEntity:
        """Persist a new subscription."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, subscription: SubscriptionEntity) -> SubscriptionEntity:
        """Update an existing subscription."""
        raise NotImplementedError

    @abstractmethod
    async def get_current_by_tenant(self, tenant_id: UUID) -> SubscriptionEntity | None:
        """Retrieve the tenant's current subscription as a single row, or None.

        One-row semantics: this is the counterpart of ``list_by_tenant`` (the
        unbounded list), not a list query.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> SubscriptionEntity | None:
        """Retrieve a subscription by its UUID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def list_expired_trials(self) -> list[SubscriptionEntity]:
        """Return all subscriptions whose trial has ended but are still active."""
        raise NotImplementedError

    @abstractmethod
    async def list_active_near_period_end(self, days_ahead: int) -> list[SubscriptionEntity]:
        """Return ACTIVE subscriptions whose current_period_end is within the
        given number of days from now (and still in the future).

        This is used by the Celery monthly billing task to proactively create
        payment preferences before the current period ends.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_gateway_subscription_id(self, gateway_subscription_id: str) -> SubscriptionEntity | None:
        """Retrieve a subscription by its gateway subscription ID, or None.

        Used by the webhook handler to resolve gateway subscription notifications
        to local SubscriptionEntity entities.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status_filter: SubscriptionStatus | None = None,
    ) -> list[SubscriptionEntity]:
        """List subscriptions for a tenant, optionally filtered by status.

        Args:
            tenant_id: The tenant UUID.
            status_filter: Optional subscription status to filter by.

        Returns:
            A list of SubscriptionEntity entities (may be empty).
        """
        raise NotImplementedError
