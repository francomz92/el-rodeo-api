"""Request schemas for billing / payment endpoints."""

from pydantic import BaseModel

from src.billing.domain.entities._plan_type import PlanType


class PlanChangeSchema(BaseModel):
    """Request body for PUT /billing/subscriptions/plan."""

    plan_type: PlanType
