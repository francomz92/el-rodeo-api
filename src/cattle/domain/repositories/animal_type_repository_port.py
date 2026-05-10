from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.common.domain.repository import IRepository


class IAnimalTypesRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> AnimalTypeEntinty | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[AnimalTypeEntinty]:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError
