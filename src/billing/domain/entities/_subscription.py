from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.billing.domain.entities._subscription_status import SubscriptionStatus


@dataclass(frozen=True)
class Subscription:
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime | None = None
    trial_end: datetime | None = None
    canceled_at: datetime | None = None
    mp_preference_id: str | None = None
    mp_subscription_id: str | None = None
    metadata: dict | None = None
