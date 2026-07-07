"""Tests for PlanType, Feature, Quota, and Plan domain entities."""

from decimal import Decimal
from uuid import uuid4

from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.value_objects._money import Money


class TestPlanType:
    """Task 1.1: PlanType enum."""

    def test_values(self) -> None:
        assert PlanType.FREE == "free"
        assert PlanType.PRO == "pro"
        assert PlanType.ENTERPRISE == "enterprise"

    def test_string_conversion(self) -> None:
        assert str(PlanType.FREE) == "free"
        assert str(PlanType.PRO) == "pro"
        assert str(PlanType.ENTERPRISE) == "enterprise"

    def test_membership(self) -> None:
        assert PlanType("free") is PlanType.FREE
        assert PlanType("pro") is PlanType.PRO
        assert PlanType("enterprise") is PlanType.ENTERPRISE


class TestFeature:
    """Task 1.2: Feature dataclass."""

    def test_construct(self) -> None:
        feature = Feature(name="csv_export")
        assert feature.name == "csv_export"
        assert feature.enabled is True

    def test_default_enabled(self) -> None:
        feature = Feature(name="csv_export", enabled=False)
        assert feature.enabled is False


class TestQuota:
    """Task 1.3: Quota dataclass."""

    def test_construct(self) -> None:
        quota = Quota(name="animals", limit=50, description="Max animals per tenant")
        assert quota.name == "animals"
        assert quota.limit == 50
        assert quota.description == "Max animals per tenant"

    def test_unlimited_minus_one(self) -> None:
        quota = Quota(name="animals", limit=-1)
        assert quota.limit == -1

    def test_default_description(self) -> None:
        quota = Quota(name="animals", limit=50)
        assert quota.description == ""


class TestPlan:
    """Task 1.4: Plan dataclass."""

    def test_construct_with_features_and_quotas(self) -> None:
        plan_id = uuid4()
        features = [Feature(name="csv_export"), Feature(name="api_access")]
        quotas = [Quota(name="animals", limit=50), Quota(name="users", limit=5)]
        plan = Plan(
            id=plan_id,
            plan_type=PlanType.PRO,
            name="Pro",
            description="Pro plan",
            features=features,
            quotas=quotas,
            price_monthly=Money(amount=Decimal("29.99")),
            price_yearly=Money(amount=Decimal("299.99")),
        )
        assert plan.id == plan_id
        assert plan.plan_type == PlanType.PRO
        assert plan.name == "Pro"
        assert plan.description == "Pro plan"
        assert plan.features == features
        assert plan.quotas == quotas
        assert plan.price_monthly == Money(amount=Decimal("29.99"))
        assert plan.price_yearly == Money(amount=Decimal("299.99"))
        assert plan.is_active is True

    def test_free_plan_defaults(self) -> None:
        plan_id = uuid4()
        plan = Plan(
            id=plan_id,
            plan_type=PlanType.FREE,
            name="Free",
            description="Free tier",
            features=[],
            quotas=[],
        )
        assert plan.price_monthly is None
        assert plan.price_yearly is None
        assert plan.is_active is True
