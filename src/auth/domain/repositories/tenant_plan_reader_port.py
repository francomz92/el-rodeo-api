from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities import PlanEntity
from src.common.domain.repository import IRepository


class ITenantPlanReader(IRepository):
    """Read-only view of the tenant's current plan.

    The billing subscription is the single source of truth for which
    plan a tenant is on; the tenant row's ``plan_id`` column is not
    maintained. Auth consumes this port instead of querying billing
    tables directly.
    """

    @abstractmethod
    async def get_current_plan_for_tenant(self, tenant_id: UUID) -> PlanEntity | None:
        """Resolve the plan behind the tenant's current subscription.

        Returns None when the tenant has no subscription row yet.
        """
        raise NotImplementedError
