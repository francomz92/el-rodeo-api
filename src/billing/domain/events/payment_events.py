"""Billing domain events."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from src.common.domain.events.base import DomainEvent


class PaymentReceived(DomainEvent):
    """Emitted when a payment is successfully received and approved."""

    def __init__(
        self,
        aggregate_id: UUID,
        payment_id: UUID | None = None,
        amount: Decimal | None = None,
        currency: str = "ARS",
        tenant_id: UUID | None = None,
        plan_type: str | None = None,
        next_billing_date: datetime | None = None,
    ) -> None:
        super().__init__(
            event_type="payment.received",
            aggregate_id=aggregate_id,
        )
        # Store additional payload fields via object.__setattr__ (frozen dataclass)
        pa_id = payment_id if payment_id is not None else aggregate_id
        amt = amount if amount is not None else Decimal("0")
        object.__setattr__(self, "payment_id", pa_id)
        object.__setattr__(self, "amount", amt)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "tenant_id", tenant_id)
        object.__setattr__(self, "plan_type", plan_type)
        object.__setattr__(self, "next_billing_date", next_billing_date)


class PaymentFailed(DomainEvent):
    """Emitted when a payment is rejected, cancelled, refunded, or charged back."""

    def __init__(
        self,
        aggregate_id: UUID,
        payment_id: UUID | None = None,
        tenant_id: UUID | None = None,
        subscription_id: UUID | None = None,
        plan_type: str | None = None,
        amount: Decimal | None = None,
        failure_reason: str | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        super().__init__(
            event_type="payment.failed",
            aggregate_id=aggregate_id,
        )
        pa_id = payment_id if payment_id is not None else aggregate_id
        amt = amount if amount is not None else Decimal("0")
        occ = occurred_at if occurred_at is not None else datetime.now(timezone.utc)
        object.__setattr__(self, "payment_id", pa_id)
        object.__setattr__(self, "tenant_id", tenant_id)
        object.__setattr__(self, "subscription_id", subscription_id)
        object.__setattr__(self, "plan_type", plan_type)
        object.__setattr__(self, "amount", amt)
        object.__setattr__(self, "failure_reason", failure_reason)
        object.__setattr__(self, "occurred_at", occ)
