"""Response schemas for billing / payment endpoints."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class SubscriptionSchema(BaseModel):
    """Output schema for a subscription."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    current_period_start: datetime
    current_period_end: datetime | None = None
    trial_end: datetime | None = None
    canceled_at: datetime | None = None
    billing_date: datetime | None = None
    gateway_card_id: str | None = None
    gateway_subscription_id: str | None = None


class PaymentSchema(BaseModel):
    """Output schema for a payment record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    amount: Decimal
    currency: str
    description: str | None = None
    payment_method: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    @field_validator("status", mode="before")
    @classmethod
    def _status_value(cls, value: object) -> object:
        return value.value if isinstance(value, Enum) else value

    @field_validator("payment_method", mode="before")
    @classmethod
    def _serialize_payment_method(cls, value: object) -> object:
        from src.billing.domain.value_objects.payment_value_objects import PaymentMethodVO

        if isinstance(value, PaymentMethodVO):
            parts = [value.card_brand or "", value.payment_type_id or ""]
            if not any(parts):
                return None
            return "|".join(parts).strip("|")
        return value


class PlanChangeResponseSchema(BaseModel):
    """Response envelope for the plan-change endpoint."""

    model_config = ConfigDict(from_attributes=True)

    subscription: SubscriptionSchema
    checkout_url: str | None = None


class PaginatedPaymentListSchema(BaseModel):
    """Response envelope for the paginated payment listing."""

    payments: list[PaymentSchema]
    total: int
    page: int
    per_page: int


__all__ = [
    "PaginatedPaymentListSchema",
    "PaymentSchema",
    "PlanChangeResponseSchema",
    "SubscriptionSchema",
]
