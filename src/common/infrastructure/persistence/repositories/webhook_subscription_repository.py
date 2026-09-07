"""SQLAlchemy implementation of IWebhookSubscriptionRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, insert, select, update

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

    async def create(self, sub: WebhookSubscription) -> WebhookSubscription:
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
        return await self.get_by_id(sub_id)  # type: ignore

    async def get_by_id(self, id: UUID) -> WebhookSubscription | None:
        stmt = select(WebhookSubscription).where(WebhookSubscription.id == id)
        stmt = self._filter_tenant(stmt)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: UUID) -> list[WebhookSubscription]:
        stmt = select(WebhookSubscription).where(WebhookSubscription.tenant_id == tenant_id).order_by(WebhookSubscription.created_at)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        id: UUID,
        url: str | None = None,
        subscribed_events: list[str] | None = None,
        is_active: bool | None = None,
    ) -> WebhookSubscription:
        values: dict = {}
        if url is not None:
            values["url"] = url
        if subscribed_events is not None:
            values["subscribed_events"] = subscribed_events
        if is_active is not None:
            values["is_active"] = is_active
        values["updated_at"] = func.now()

        stmt = update(WebhookSubscription).where(WebhookSubscription.id == id).values(**values)
        stmt = self._filter_tenant(stmt)
        await self.db.execute(stmt)

        # Re-fetch the updated row
        updated = await self.get_by_id(id)
        return updated  # type: ignore

    async def delete(self, id: UUID) -> None:
        stmt = delete(WebhookSubscription).where(WebhookSubscription.id == id)
        stmt = self._filter_tenant(stmt)
        await self.db.execute(stmt)

    async def list_all_active(self) -> list[WebhookSubscription]:
        """Return all active subscriptions across all tenants."""
        stmt = select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True)).order_by(WebhookSubscription.created_at)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
