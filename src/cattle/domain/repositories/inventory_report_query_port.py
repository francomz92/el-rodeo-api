from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IAnimalInventoryReportQuery(IRepository):
    @abstractmethod
    async def get_inventory_summary(self, *, tenant_id: UUID) -> dict:
        """Return animal counts grouped by status and by type."""
        ...
