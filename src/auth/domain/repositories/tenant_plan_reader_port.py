from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities import PlanEntity
from src.common.domain.repository import IRepository


class ITenantPlanReader(IRepository):
    @abstractmethod
    async def get_by_id(self, plan_id: UUID) -> PlanEntity | None:
        """Retrieve a tenant's plan by its persisted identifier."""
        raise NotImplementedError
