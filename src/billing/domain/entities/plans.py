from dataclasses import dataclass
from uuid import UUID

from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.value_objects.payment_value_objects import MoneyVO


@dataclass(frozen=True)
class FeatureEntity:
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class QuotaEntity:
    name: str
    limit: int
    description: str = ""


@dataclass(frozen=True)
class PlanEntity:
    """Plan aggregate root.

    Canonical persisted shape of the JSONB ``features``/``quotas`` columns
    (F2-5 map #8): ``features`` is a ``list[str]`` of feature names and
    ``quotas`` is a ``list[dict]`` whose entries carry ``name``/``limit`` and
    an optional ``description``. ``build_plan``
    (``infrastructure/persistence/repositories/mappers.py``) maps those rows
    onto the ``FeatureEntity``/``QuotaEntity`` lists below and also accepts
    the legacy variant with dict-shaped features and description-less quotas.
    """

    id: UUID
    plan_type: PlanTypeEntity
    name: str
    description: str
    features: list[FeatureEntity]
    quotas: list[QuotaEntity]
    price_monthly: MoneyVO | None = None
    price_yearly: MoneyVO | None = None
    is_active: bool = True
