from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.domain.entities._plan import PlanEntity
from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.billing.domain.repositories import IPlanRepository
from src.billing.infrastructure.persistence.models import Plan
from src.billing.infrastructure.persistence.repositories._mappers import build_plan

# Sequential deterministic UUIDs for seed data — stable across test runs and sessions.
_FREE_PLAN_ID = UUID("00000000-0000-0000-0000-000000000001")
_PRO_PLAN_ID = UUID("b466e7e4-bcbe-42ec-9b11-126ae8a8e69c")
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

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # self._plans: dict[PlanTypeEntity, PlanEntity] = self._seed_plans()

    # @staticmethod
    # def _seed_plans() -> dict[PlanTypeEntity, PlanEntity]:
    #     return {
    #         PlanTypeEntity.FREE: PlanEntity(
    #             id=_FREE_PLAN_ID,
    #             plan_type=PlanTypeEntity.FREE,
    #             name="Free",
    #             description="Free tier — para pequeños productores",
    #             features=[
    #                 FeatureEntity(name="basic_tracking"),
    #             ],
    #             quotas=[
    #                 QuotaEntity(name="tenants", limit=1, description="Máximo 1 tenant"),
    #                 QuotaEntity(name="animals", limit=50, description="Máximo 50 animales"),
    #                 QuotaEntity(name="sales", limit=100, description="Máximo 100 ventas/mes"),
    #                 QuotaEntity(name="users", limit=5, description="Máximo 5 usuarios"),
    #             ],
    #             price_monthly=MoneyVO(amount=Decimal("0.00")),
    #             price_yearly=None,
    #         ),
    #         PlanTypeEntity.PRO: PlanEntity(
    #             id=_PRO_PLAN_ID,
    #             plan_type=PlanTypeEntity.PRO,
    #             name="Pro",
    #             description="Plan profesional para medianos productores",
    #             features=[
    #                 FeatureEntity(name="basic_tracking"),
    #                 FeatureEntity(name="csv_export"),
    #                 FeatureEntity(name="api_access"),
    #             ],
    #             quotas=[
    #                 QuotaEntity(name="tenants", limit=3, description="Máximo 3 tenants"),
    #                 QuotaEntity(name="animals", limit=500, description="Máximo 500 animales"),
    #                 QuotaEntity(name="sales", limit=1000, description="Máximo 1000 ventas/mes"),
    #                 QuotaEntity(name="users", limit=25, description="Máximo 25 usuarios"),
    #             ],
    #             price_monthly=MoneyVO(amount=Decimal("15.00")),
    #             price_yearly=MoneyVO(amount=Decimal("150.00")),
    #         ),
    #         PlanTypeEntity.ENTERPRISE: PlanEntity(
    #             id=_ENTERPRISE_PLAN_ID,
    #             plan_type=PlanTypeEntity.ENTERPRISE,
    #             name="Enterprise",
    #             description="Plan empresarial — acceso completo",
    #             features=[
    #                 FeatureEntity(name="basic_tracking"),
    #                 FeatureEntity(name="csv_export"),
    #                 FeatureEntity(name="api_access"),
    #                 FeatureEntity(name="white_label"),
    #                 FeatureEntity(name="priority_support"),
    #             ],
    #             quotas=[
    #                 QuotaEntity(name="tenants", limit=-1, description="Ilimitado"),
    #                 QuotaEntity(name="animals", limit=-1, description="Ilimitado"),
    #                 QuotaEntity(name="sales", limit=-1, description="Ilimitado"),
    #                 QuotaEntity(name="users", limit=-1, description="Ilimitado"),
    #             ],
    #             price_monthly=MoneyVO(amount=Decimal("50.00")),
    #             price_yearly=MoneyVO(amount=Decimal("500.00")),
    #         ),
    #     }

    async def get_by_plan_type(self, plan_type: PlanTypeEntity) -> PlanEntity | None:
        query = select(*Plan.__table__.columns).where(Plan.plan_type == plan_type.value)
        result = await self.db.execute(query)
        plan_model = result.mappings().one_or_none()
        if plan_model is None:
            return None
        return build_plan(plan_model)

    async def get_by_id(self, id: UUID) -> PlanEntity | None:
        query = select(*Plan.__table__.columns).where(Plan.id == id)
        result = await self.db.execute(query)
        plan_model = result.mappings().one_or_none()
        if plan_model is None:
            return None
        return build_plan(plan_model)

    async def list_all(self) -> list[PlanEntity]:
        query = select(*Plan.__table__.columns)
        result = await self.db.execute(query)
        plan_models = result.mappings().all()
        return [build_plan(plan_model) for plan_model in plan_models]
