"""Mapper functions for UserRepository.

Extracted from user_repository.py to reduce file size (task 3.4 of
modularizacion-estructura).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import RowMapping

from src.billing.domain.entities import FeatureEntity, PlanEntity, PlanTypeEntity, QuotaEntity
from src.billing.domain.value_objects import MoneyVO


def build_plan(plan_db: RowMapping) -> PlanEntity:
    """Build a PlanEntity from a SQLAlchemy RowMapping."""
    return PlanEntity(
        id=plan_db["id"],
        plan_type=PlanTypeEntity(plan_db["plan_type"]),
        name=plan_db["name"],
        description=plan_db["description"],
        features=[FeatureEntity(name=feature) for feature in plan_db["features"]],
        quotas=[QuotaEntity(name=quota["name"], limit=quota["limit"], description=quota["description"]) for quota in plan_db["quotas"]],
        price_monthly=MoneyVO(amount=Decimal(str(plan_db["price_monthly"]))) if plan_db["price_monthly"] is not None else None,
        price_yearly=MoneyVO(amount=Decimal(str(plan_db["price_yearly"]))) if plan_db["price_yearly"] is not None else None,
        is_active=plan_db["is_active"],
    )


def json_safe(value: object) -> object:
    """Convert non-JSON-serializable values to strings."""
    if isinstance(value, (UUID, datetime)):
        return str(value)
    return value
