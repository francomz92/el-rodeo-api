"""Billing domain events."""

from decimal import Decimal
from typing import Any
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
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type="payment.received",
            aggregate_id=aggregate_id,
            **kwargs,
        )
        # Store additional payload fields via object.__setattr__ (frozen dataclass)
        pa_id = payment_id if payment_id is not None else aggregate_id
        amt = amount if amount is not None else Decimal("0")
        object.__setattr__(self, "payment_id", pa_id)
        object.__setattr__(self, "amount", amt)
        object.__setattr__(self, "currency", currency)
