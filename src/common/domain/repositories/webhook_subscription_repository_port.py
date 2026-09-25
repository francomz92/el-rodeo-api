"""Repository port for WebhookSubscription persistence."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.entities.webhook_subscription import (
    WebhookSubscriptionCreateData,
    WebhookSubscriptionEntity,
)
from src.common.domain.repository import IRepository


class IWebhookSubscriptionRepository(IRepository):
    """Interface for webhook subscription data access."""

    @abstractmethod
    async def create(self, sub: WebhookSubscriptionCreateData) -> WebhookSubscriptionEntity:
        """Persist a new webhook subscription and return its domain entity."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> WebhookSubscriptionEntity | None:
        """Retrieve a subscription by its ID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[WebhookSubscriptionEntity]:
        """List all subscriptions for a tenant, ordered by creation date."""
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        id: UUID,
        url: str | None = None,
        subscribed_events: list[str] | None = None,
        is_active: bool | None = None,
        failure_count: int | None = None,
    ) -> WebhookSubscriptionEntity:
        """Partially update a subscription and return the updated entity."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Delete a subscription by its ID."""
        raise NotImplementedError

    @abstractmethod
    async def list_all_active(self) -> list[WebhookSubscriptionEntity]:
        """Return all active subscriptions across all tenants (admin query).

        Used by the outbox forwarder task to match pending events against
        active subscribers.  This is a cross-tenant query that bypasses
        the tenant filter.
        """
        raise NotImplementedError
