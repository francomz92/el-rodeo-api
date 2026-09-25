"""SQLAlchemy implementation of IWebhookSubscriptionRepository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, insert, select, update

from src.common.domain.entities.webhook_subscription import (
    WebhookSubscriptionCreateData,
    WebhookSubscriptionEntity,
)
from src.common.domain.repositories.webhook_subscription_repository_port import (
    IWebhookSubscriptionRepository,
)
from src.common.infrastructure.persistence.models import WebhookSubscription
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class WebhookSubscriptionRepository(
    IWebhookSubscriptionRepository,
    TenantAwareRepository,
):
    """SQLAlchemy async implementation scoped by tenant_id."""

    _model: type[WebhookSubscription] = WebhookSubscription

    @staticmethod
    def _to_entity(model: WebhookSubscription) -> WebhookSubscriptionEntity:
        return WebhookSubscriptionEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            url=model.url,
            secret=model.secret,
            subscribed_events=model.subscribed_events,
            is_active=model.is_active,
            failure_count=model.failure_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def create(self, sub: WebhookSubscriptionCreateData) -> WebhookSubscriptionEntity:
        stmt = (
            insert(WebhookSubscription)
            .values(
                tenant_id=sub.tenant_id,
                url=sub.url,
                secret=sub.secret,
                subscribed_events=sub.subscribed_events,
            )
            .returning(WebhookSubscription.id)
        )
        result = await self.db.execute(stmt)
        sub_id = result.scalar_one()
        created = await self.get_by_id(sub_id)
        return created  # type: ignore[return-value]

    async def get_by_id(self, id: UUID) -> WebhookSubscriptionEntity | None:
        stmt = select(WebhookSubscription).where(WebhookSubscription.id == id)
        stmt = self._filter_tenant(stmt)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def list_by_tenant(self, tenant_id: UUID) -> list[WebhookSubscriptionEntity]:
        stmt = select(WebhookSubscription).where(WebhookSubscription.tenant_id == tenant_id).order_by(WebhookSubscription.created_at)
        result = await self.db.execute(stmt)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(
        self,
        id: UUID,
        url: str | None = None,
        subscribed_events: list[str] | None = None,
        is_active: bool | None = None,
        failure_count: int | None = None,
    ) -> WebhookSubscriptionEntity:
        values: dict[str, Any] = {}
        if url is not None:
            values["url"] = url
        if subscribed_events is not None:
            values["subscribed_events"] = subscribed_events
        if is_active is not None:
            values["is_active"] = is_active
        if failure_count is not None:
            values["failure_count"] = failure_count
        values["updated_at"] = func.now()

        stmt = update(WebhookSubscription).where(WebhookSubscription.id == id).values(**values)
        stmt = self._filter_tenant(stmt)
        await self.db.execute(stmt)

        # Re-fetch the updated row and return it as a detached domain entity.
        updated = await self.get_by_id(id)
        return updated  # type: ignore[return-value]

    async def delete(self, id: UUID) -> None:
        stmt = delete(WebhookSubscription).where(WebhookSubscription.id == id)
        stmt = self._filter_tenant(stmt)
        await self.db.execute(stmt)

    async def list_all_active(self) -> list[WebhookSubscriptionEntity]:
        """Return all active subscriptions across all tenants."""
        stmt = select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True)).order_by(WebhookSubscription.created_at)
        result = await self.db.execute(stmt)
        return [self._to_entity(model) for model in result.scalars().all()]
