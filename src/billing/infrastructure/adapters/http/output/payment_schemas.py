"""Response schemas for billing / payment endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SubscriptionSchema(BaseModel):
    """Output schema for a subscription."""

    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    current_period_start: datetime
    current_period_end: datetime | None = None
    next_billing_date: datetime | None = None
    billing_date: datetime | None = None
    gateway_card_id: str | None = None
    gateway_subscription_id: str | None = None


class PaymentSchema(BaseModel):
    """Output schema for a payment record."""

    id: UUID
    status: str
    amount: Decimal
    currency: str
    description: str | None = None
    payment_method: str | None = None
    paid_at: datetime | None = None
    created_at: datetime
