from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty


class ISupplyTypesRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> SupplyTypeEntinty | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[SupplyTypeEntinty]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
