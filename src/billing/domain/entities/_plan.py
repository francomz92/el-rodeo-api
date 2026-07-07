from dataclasses import dataclass
from uuid import UUID

from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.value_objects._money import Money


@dataclass(frozen=True)
class Plan:
    id: UUID
    plan_type: PlanType
    name: str
    description: str
    features: list[Feature]
    quotas: list[Quota]
    price_monthly: Money | None = None
    price_yearly: Money | None = None
    is_active: bool = True
