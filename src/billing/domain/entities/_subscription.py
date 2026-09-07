from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
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
    billing_date: datetime | None = None
    next_billing_date: datetime | None = None
    gateway_preference_id: str | None = None
    gateway_subscription_id: str | None = None
    gateway_card_id: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.status == SubscriptionStatus.ACTIVE and self.current_period_end is None:
            raise ValueError("ACTIVE subscription must have a current_period_end")
        if self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE) and self.current_period_end is None:
            raise ValueError(f"{self.status.value} subscription must have a current_period_end")

    def is_active(self) -> bool:
        """Return True if the subscription is in an active or trial state."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL)

    def is_expired(self) -> bool:
        """Return True if the subscription is expired or past its period end."""
        if self.status in (SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELED):
            return True
        if self.current_period_end is not None and datetime.now(tz=timezone.utc) > self.current_period_end:
            return True
        return False

    def can_cancel(self) -> bool:
        """Return True if the subscription can be cancelled."""
        return self.status not in (SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED)

    def mark_as_canceled(self) -> "Subscription":
        """Return a new Subscription with status set to CANCELED."""
        from dataclasses import replace

        return replace(
            self,
            status=SubscriptionStatus.CANCELED,
            canceled_at=datetime.now(tz=timezone.utc),
        )
