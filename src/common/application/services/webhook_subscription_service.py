"""Application service for tenant-scoped WebhookSubscription management."""

from __future__ import annotations

import secrets
from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError
from src.common.domain.repositories.webhook_subscription_repository_port import (
    IWebhookSubscriptionRepository,
)
from src.common.infrastructure.persistence.models.webhook_subscription import (
    WebhookSubscription,
)
from src.common.infrastructure.security.fernet_engine import FernetEngine


class WebhookSubscriptionService:
    """Application service for webhook subscription CRUD operations.

    Delegates data access to ``IWebhookSubscriptionRepository`` through
    the Unit of Work, keeping the service focused on orchestration and
    business rules (secret generation, tenant ownership, 404 handling).

    Secrets are encrypted at rest via ``FernetEngine`` before storage
    and decrypted on read.
    """

    def __init__(self, uow: IUoW) -> None:
        self._uow = uow

    @property
    def _repo(self) -> IWebhookSubscriptionRepository:
        return self._uow.get_repository(IWebhookSubscriptionRepository)

    async def create(self, tenant_id: UUID, url: str, subscribed_events: list[str]) -> WebhookSubscription:
        plain_secret = secrets.token_urlsafe(32)
        sub = WebhookSubscription(
            tenant_id=tenant_id,
            url=url,
            secret=FernetEngine.encrypt_secret(plain_secret),
            subscribed_events=subscribed_events,
        )
        created = await self._repo.create(sub)
        await self._uow.commit()
        await self._uow.refresh(created)
        # Return the model with the plaintext secret — bypass SQLAlchemy
        # instrumentation to prevent dirty write-back on future commits.
        object.__setattr__(created, "secret", plain_secret)
        return created

    async def list_for_tenant(self, tenant_id: UUID) -> list[WebhookSubscription]:
        return await self._repo.list_by_tenant(tenant_id)

    async def _verify_ownership(self, subscription_id: UUID, tenant_id: UUID) -> WebhookSubscription:
        """Check ownership without decrypting the secret.

        Raises ``NotFoundError`` when the subscription does not exist or
        belongs to a different tenant.  Returns the ORM-tracked model
        **without** mutating its ``secret`` column.
        """
        sub = await self._repo.get_by_id(subscription_id)
        if sub is None or sub.tenant_id != tenant_id:
            raise NotFoundError(message="Webhook subscription not found")
        return sub

    async def get_by_id_for_tenant(self, subscription_id: UUID, tenant_id: UUID) -> WebhookSubscription:
        sub = await self._verify_ownership(subscription_id, tenant_id)
        # Decrypt the secret WITHOUT mutating the ORM-tracked column:
        # writing ``sub.secret = plaintext`` on a session-tracked model
        # would flush the plaintext to the DB on the next ``commit()``.
        if sub.secret:
            decrypted = FernetEngine.decrypt_secret(sub.secret)
            # Bypass SQLAlchemy attribute instrumentation so the change
            # is NOT tracked as dirty.  The decrypted value is visible
            # to the caller (router / response serialisation) but will
            # never be written back to the database.
            object.__setattr__(sub, "secret", decrypted)
        return sub

    async def update(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
        url: str | None = None,
        subscribed_events: list[str] | None = None,
        is_active: bool | None = None,
    ) -> WebhookSubscription:
        await self._verify_ownership(subscription_id, tenant_id)

        updated = await self._repo.update(
            subscription_id,
            url=url,
            subscribed_events=subscribed_events,
            is_active=is_active,
        )
        await self._uow.commit()
        return updated

    async def delete(self, subscription_id: UUID, tenant_id: UUID) -> None:
        await self._verify_ownership(subscription_id, tenant_id)

        await self._repo.delete(subscription_id)
        await self._uow.commit()
