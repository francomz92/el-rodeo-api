from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities._plan import PlanEntity
from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.common.domain.repository import IRepository


class IPlanRepository(IRepository):
    @abstractmethod
    async def get_by_plan_type(self, plan_type: PlanTypeEntity) -> PlanEntity | None:
        """Retrieve a plan by its PlanType."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> PlanEntity | None:
        """Retrieve a plan by its UUID, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[PlanEntity]:
        """List all available plans."""
        raise NotImplementedError
