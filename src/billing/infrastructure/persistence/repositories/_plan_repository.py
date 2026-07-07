from decimal import Decimal
from uuid import UUID

from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.repositories import IPlanRepository
from src.billing.domain.value_objects import Money

# Deterministic UUIDs for seed data — stable across test runs and sessions.
# These are namespace-based UUIDs derived from the plan type name.
_FREE_PLAN_ID = UUID("00000000-0000-0000-0000-000000000001")
_PRO_PLAN_ID = UUID("00000000-0000-0000-0000-000000000002")
_ENTERPRISE_PLAN_ID = UUID("00000000-0000-0000-0000-000000000003")


class PlanRepository(IPlanRepository):
    """Seed-data PlanRepository for Phase 7.1.

    Plans are stored in an in-memory dict rather than read from the DB.
    This matches the immutable seed-data constraint — plans change only
    via migration, and DB reads will replace this in a later phase.

    Plan IDs are deterministic (see ``_FREE_PLAN_ID``, ``_PRO_PLAN_ID``,
    ``_ENTERPRISE_PLAN_ID``) so that integration tests referencing plans
    by ID work consistently across sessions.
    """

    def __init__(self) -> None:
        self._plans: dict[PlanType, Plan] = self._seed_plans()

    @staticmethod
    def _seed_plans() -> dict[PlanType, Plan]:
        return {
            PlanType.FREE: Plan(
                id=_FREE_PLAN_ID,
                plan_type=PlanType.FREE,
                name="Free",
                description="Free tier — para pequeños productores",
                features=[
                    Feature(name="basic_tracking"),
                ],
                quotas=[
                    Quota(name="tenants", limit=1, description="Máximo 1 tenant"),
                    Quota(name="animals", limit=50, description="Máximo 50 animales"),
                    Quota(name="sales", limit=100, description="Máximo 100 ventas/mes"),
                    Quota(name="users", limit=5, description="Máximo 5 usuarios"),
                ],
                price_monthly=Money(amount=Decimal("0.00")),
                price_yearly=None,
            ),
            PlanType.PRO: Plan(
                id=_PRO_PLAN_ID,
                plan_type=PlanType.PRO,
                name="Pro",
                description="Plan profesional para medianos productores",
                features=[
                    Feature(name="basic_tracking"),
                    Feature(name="csv_export"),
                    Feature(name="api_access"),
                ],
                quotas=[
                    Quota(name="tenants", limit=3, description="Máximo 3 tenants"),
                    Quota(name="animals", limit=500, description="Máximo 500 animales"),
                    Quota(name="sales", limit=1000, description="Máximo 1000 ventas/mes"),
                    Quota(name="users", limit=25, description="Máximo 25 usuarios"),
                ],
                price_monthly=Money(amount=Decimal("15.00")),
                price_yearly=Money(amount=Decimal("150.00")),
            ),
            PlanType.ENTERPRISE: Plan(
                id=_ENTERPRISE_PLAN_ID,
                plan_type=PlanType.ENTERPRISE,
                name="Enterprise",
                description="Plan empresarial — acceso completo",
                features=[
                    Feature(name="basic_tracking"),
                    Feature(name="csv_export"),
                    Feature(name="api_access"),
                    Feature(name="white_label"),
                    Feature(name="priority_support"),
                ],
                quotas=[
                    Quota(name="tenants", limit=-1, description="Ilimitado"),
                    Quota(name="animals", limit=-1, description="Ilimitado"),
                    Quota(name="sales", limit=-1, description="Ilimitado"),
                    Quota(name="users", limit=-1, description="Ilimitado"),
                ],
                price_monthly=Money(amount=Decimal("50.00")),
                price_yearly=Money(amount=Decimal("500.00")),
            ),
        }

    async def get_by_plan_type(self, plan_type: PlanType) -> Plan:
        return self._plans[plan_type]

    async def get_by_id(self, id: UUID) -> Plan | None:
        for plan in self._plans.values():
            if plan.id == id:
                return plan
        return None

    async def list_all(self) -> list[Plan]:
        return list(self._plans.values())
