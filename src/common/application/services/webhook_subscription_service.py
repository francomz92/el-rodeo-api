"""Application service for tenant-scoped WebhookSubscription management."""

from __future__ import annotations

import secrets
from uuid import UUID

from src.common.application.ports.secret_cipher import SecretCipher
from src.common.application.ports.uow import IUoW
from src.common.domain.entities.webhook_subscription import (
    WebhookSubscriptionCreateData,
    WebhookSubscriptionEntity,
)
from src.common.domain.exceptions import NotFoundError
from src.common.domain.repositories.webhook_subscription_repository_port import (
    IWebhookSubscriptionRepository,
)


class WebhookSubscriptionService:
    """Application service for webhook subscription CRUD operations.

    Delegates data access to ``IWebhookSubscriptionRepository`` through
    the Unit of Work, keeping the service focused on orchestration and
    business rules (secret generation, tenant ownership, 404 handling).

    Secrets are encrypted at rest via the injected ``SecretCipher`` before storage
    and decrypted on read.
    """

    def __init__(self, uow: IUoW, secret_cipher: SecretCipher) -> None:
        self._uow = uow
        self._secret_cipher = secret_cipher

    @property
    def _repo(self) -> IWebhookSubscriptionRepository:
        return self._uow.get_repository(IWebhookSubscriptionRepository)

    async def create(self, tenant_id: UUID, url: str, subscribed_events: list[str]) -> WebhookSubscriptionEntity:
        plain_secret = secrets.token_urlsafe(32)
        sub = WebhookSubscriptionCreateData(
            tenant_id=tenant_id,
            url=url,
            secret=self._secret_cipher.encrypt_secret(plain_secret),
            subscribed_events=subscribed_events,
        )
        created = await self._repo.create(sub)
        await self._uow.commit()
        # The repository returned a detached domain dataclass, so plaintext
        # response data cannot be written back through ORM dirty tracking.
        created.secret = plain_secret
        return created

    async def list_for_tenant(self, tenant_id: UUID) -> list[WebhookSubscriptionEntity]:
        return await self._repo.list_by_tenant(tenant_id)

    async def _verify_ownership(self, subscription_id: UUID, tenant_id: UUID) -> WebhookSubscriptionEntity:
        """Check ownership without decrypting the secret.

        Raises ``NotFoundError`` when the subscription does not exist or
        belongs to a different tenant.
        """
        sub = await self._repo.get_by_id(subscription_id)
        if sub is None or sub.tenant_id != tenant_id:
            raise NotFoundError(message="Webhook subscription not found")
        return sub

    async def get_by_id_for_tenant(self, subscription_id: UUID, tenant_id: UUID) -> WebhookSubscriptionEntity:
        sub = await self._verify_ownership(subscription_id, tenant_id)
        # Return plaintext to the API without altering persisted encrypted data.
        if sub.secret:
            sub.secret = self._secret_cipher.decrypt_secret(sub.secret)
        return sub

    async def update(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
        url: str | None = None,
        subscribed_events: list[str] | None = None,
        is_active: bool | None = None,
    ) -> WebhookSubscriptionEntity:
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
