from dataclasses import dataclass
from uuid import UUID

from src.billing.domain.entities._feature import FeatureEntity
from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.billing.domain.entities._quota import QuotaEntity
from src.billing.domain.value_objects._money import MoneyVO


@dataclass(frozen=True)
class PlanEntity:
    id: UUID
    plan_type: PlanTypeEntity
    name: str
    description: str
    features: list[FeatureEntity]
    quotas: list[QuotaEntity]
    price_monthly: MoneyVO | None = None
    price_yearly: MoneyVO | None = None
    is_active: bool = True
