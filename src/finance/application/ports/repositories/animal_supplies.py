from abc import abstractmethod
from uuid import UUID

from src.common.application.ports.repository import IRepository
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity


class IAnimalSuppliesRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> AnimalSupplyEntity | None:
        raise NotImplemented

    @abstractmethod
    async def list_all(self, user_id: UUID) -> list[AnimalSupplyEntity]:
        raise NotImplemented

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        type_id: UUID,
        name: str,
        description: str,
        amount: float,
        critical_amount: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        name: str,
        description: str,
        amount: float,
        critical_amount: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        raise NotImplemented

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplemented
