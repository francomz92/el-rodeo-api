"""Domain types for webhook subscriptions."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class WebhookSubscriptionEntity:
    """Webhook subscription data returned by the repository boundary."""

    id: UUID
    tenant_id: UUID
    url: str
    secret: str
    subscribed_events: list[str]
    is_active: bool
    failure_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WebhookSubscriptionCreateData:
    """Encrypted webhook subscription data required before insertion."""

    tenant_id: UUID
    url: str
    secret: str
    subscribed_events: list[str]
