"""Response schemas for billing / payment endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
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


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    per_page: int
