from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from src.billing.domain.entities._payment_status import PaymentStatus


@dataclass(frozen=True)
class PaymentMethod:
    card_brand: str | None = None
    payment_type_id: str | None = None


@dataclass(frozen=True)
class Payment:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default=UUID(int=0))
    subscription_id: UUID = field(default=UUID(int=0))
    status: PaymentStatus = field(default=PaymentStatus.PENDING)
    amount: Decimal = field(default=Decimal("0"))
    mp_payment_id: str | None = None
    mp_preference_id: str | None = None
    currency: str = "ARS"
    description: str | None = None
    payment_method: PaymentMethod | None = None
    installments: int | None = None
    paid_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime | None = None
