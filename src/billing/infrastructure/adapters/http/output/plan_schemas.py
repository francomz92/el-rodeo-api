from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.billing.domain.entities import FeatureEntity, PlanTypeEntity, QuotaEntity
from src.billing.domain.value_objects import MoneyVO


class PlanResponseSchema(BaseModel):
    id: UUID
    plan_type: PlanTypeEntity
    name: str
    description: Optional[str]
    features: list[FeatureEntity]
    quotas: list[QuotaEntity]
    price_monthly: MoneyVO
    price_yearly: MoneyVO
    is_active: bool
