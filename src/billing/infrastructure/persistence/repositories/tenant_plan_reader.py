from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.domain.repositories.tenant_plan_reader_port import ITenantPlanReader
from src.billing.domain.entities import PlanEntity
from src.billing.infrastructure.persistence.models import Plan


class TenantPlanReader(ITenantPlanReader):
    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_by_id(self, plan_id: UUID) -> PlanEntity | None:
        stmt = select(
            Plan.id.label("plan_id"),
            Plan.plan_type.label("plan_type"),
            Plan.name.label("plan_name"),
            Plan.description.label("plan_description"),
            Plan.features.label("plan_features"),
            Plan.quotas.label("plan_quotas"),
            Plan.price_monthly.label("plan_price_monthly"),
            Plan.price_yearly.label("plan_price_yearly"),
            Plan.is_active.label("plan_is_active"),
        ).where(Plan.id == plan_id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        if row is None:
            return None
        return PlanEntity(
            id=row["plan_id"],
            plan_type=row["plan_type"],
            name=row["plan_name"],
            description=row["plan_description"],
            features=row["plan_features"],
            quotas=row["plan_quotas"],
            price_monthly=row["plan_price_monthly"],
            price_yearly=row["plan_price_yearly"],
            is_active=row["plan_is_active"],
        )
