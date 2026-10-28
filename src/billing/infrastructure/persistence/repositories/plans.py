from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.entities.plans import PlanEntity
from src.billing.domain.repositories import IPlanRepository
from src.billing.infrastructure.persistence.models import Plan

from .mappers import build_plan


class PlanRepository(IPlanRepository):
    """SQLAlchemy implementation of IPlanRepository.

    Plans live in the DB (seeded out-of-band, no migration seeds them yet).
    Note: get_by_plan_type does not filter by is_active today.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

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
