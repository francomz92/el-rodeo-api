from abc import abstractmethod
from uuid import UUID

from src.common.application.ports.repository import IRepository
from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty


class ISupplyTypesRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> SupplyTypeEntinty | None:
        raise NotImplemented

    @abstractmethod
    async def list_all(self) -> list[SupplyTypeEntinty]:
        raise NotImplemented

    @abstractmethod
    async def create(self, name: str) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_data(self, id: UUID, name: str) -> None:
        raise NotImplemented

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplemented
