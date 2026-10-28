from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.domain.repositories.tenant_plan_reader_port import ITenantPlanReader
from src.billing.domain.entities import PlanEntity
from src.billing.infrastructure.persistence.models import Plan
from src.billing.infrastructure.persistence.models._subscriptions import Subscription
from src.billing.infrastructure.persistence.repositories.mappers import build_plan


class TenantPlanReader(ITenantPlanReader):
    """Resolve the tenant's current plan from its latest subscription row."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_current_plan_for_tenant(self, tenant_id: UUID) -> PlanEntity | None:
        stmt = (
            select(*Plan.__table__.columns)
            .join(Subscription, Subscription.plan_id == Plan.id)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.current_period_start.desc())
            .limit(1)
        )
        row = (await self.db.execute(stmt)).mappings().one_or_none()
        if row is None:
            return None
        return build_plan(row)
