from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.common.domain.repository import IRepository


class IPlanRepository(IRepository):
    @abstractmethod
    async def get_by_plan_type(self, plan_type: PlanType) -> Plan:
        """Retrieve a plan by its PlanType."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Plan | None:
        """Retrieve a plan by its UUID, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Plan]:
        """List all available plans."""
        raise NotImplementedError
