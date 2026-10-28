"""Row-to-entity builders for the billing repositories."""

from decimal import Decimal

from sqlalchemy import RowMapping

from src.billing.domain.constants.payments import PaymentStatus
from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities import (
    FeatureEntity,
    PaymentEntity,
    PlanEntity,
    PlanTypeEntity,
    QuotaEntity,
    SubscriptionEntity,
)
from src.billing.domain.value_objects import MoneyVO, PaymentMethodVO


def build_subscription(row: RowMapping) -> SubscriptionEntity:
    """Build a SubscriptionEntity from a subscriptions row mapping."""
    return SubscriptionEntity(
        id=row["id"],
        tenant_id=row["tenant_id"],
        plan_id=row["plan_id"],
        status=SubscriptionStatus(row["status"]),
        current_period_start=row["current_period_start"],
        current_period_end=row.get("current_period_end"),
        trial_end=row.get("trial_end"),
        canceled_at=row.get("canceled_at"),
        metadata=row.get("subscription_metadata"),
        gateway_preference_id=row.get("gateway_preference_id"),
        gateway_subscription_id=row.get("gateway_subscription_id"),
        billing_date=row.get("billing_date"),
        next_billing_date=row.get("next_billing_date"),
        gateway_card_id=row.get("gateway_card_id"),
    )


def build_payment(row: RowMapping) -> PaymentEntity:
    """Build a PaymentEntity from a payments row mapping."""
    raw_method = row.get("payment_method")
    payment_method: PaymentMethodVO | None = None
    if raw_method and "|" in raw_method:
        parts = raw_method.split("|", 1)
        payment_method = PaymentMethodVO(
            card_brand=parts[0] or None,
            payment_type_id=parts[1] or None,
        )

    return PaymentEntity(
        id=row["id"],
        tenant_id=row["tenant_id"],
        subscription_id=row["subscription_id"],
        mp_payment_id=row.get("mp_payment_id"),
        mp_preference_id=row.get("mp_preference_id"),
        status=PaymentStatus(row["status"]),
        amount=Decimal(str(row["amount"])),
        currency=row.get("currency", "ARS"),
        description=row.get("description"),
        payment_method=payment_method,
        installments=row.get("installments"),
        paid_at=row.get("paid_at"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def build_plan(plan_db: RowMapping) -> PlanEntity:
    """Build a PlanEntity from a SQLAlchemy RowMapping.

    Tolerates the legacy dual shape of the JSONB ``features``/``quotas``
    columns (F2-5 map #8): ``features`` may hold plain names (``list[str]``)
    or serialized entities (``list[dict]`` with ``name``/``enabled``), and
    ``quotas`` entries may omit ``description``. The canonical persisted
    shape is documented on ``PlanEntity``.
    """
    return PlanEntity(
        id=plan_db["id"],
        plan_type=PlanTypeEntity(plan_db["plan_type"]),
        name=plan_db["name"],
        description=plan_db["description"],
        features=_build_features(plan_db["features"]),
        quotas=_build_quotas(plan_db["quotas"]),
        price_monthly=MoneyVO(amount=Decimal(str(plan_db["price_monthly"]))) if plan_db["price_monthly"] is not None else None,
        price_yearly=MoneyVO(amount=Decimal(str(plan_db["price_yearly"]))) if plan_db["price_yearly"] is not None else None,
        is_active=plan_db["is_active"],
    )


def _build_features(raw_features: object) -> list[FeatureEntity]:
    """Map the JSONB ``features`` column, tolerating str or dict entries."""
    if not raw_features:
        return []
    features: list[FeatureEntity] = []
    for feature in raw_features:  # type: ignore[union-attr]
        if isinstance(feature, dict):
            features.append(FeatureEntity(name=str(feature.get("name", "")), enabled=bool(feature.get("enabled", True))))
        else:
            features.append(FeatureEntity(name=str(feature)))
    return features


def _build_quotas(raw_quotas: object) -> list[QuotaEntity]:
    """Map the JSONB ``quotas`` column, tolerating a missing ``description``."""
    if not raw_quotas:
        return []
    quotas: list[QuotaEntity] = []
    for quota in raw_quotas:  # type: ignore[union-attr]
        if isinstance(quota, dict):
            quotas.append(
                QuotaEntity(
                    name=str(quota.get("name", "")),
                    limit=int(quota.get("limit", 0)),
                    description=str(quota.get("description") or ""),
                )
            )
    return quotas
