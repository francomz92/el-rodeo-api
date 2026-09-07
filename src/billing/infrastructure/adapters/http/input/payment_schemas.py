"""Request schemas for billing / payment endpoints."""

from pydantic import BaseModel

from src.billing.domain.entities._plan_type import PlanTypeEntity


class PlanChangeSchema(BaseModel):
    """Request body for PUT /billing/subscriptions/plan."""

    plan_type: PlanTypeEntity


class CreateSubscriptionSchema(BaseModel):
    """Request body for POST /billing/subscriptions."""

    plan_type: PlanTypeEntity
    card_token_id: str


class UpdatePaymentMethodSchema(BaseModel):
    """Request body for POST /billing/subscriptions/{id}/payment-method."""

    card_token_id: str
