from abc import abstractmethod
from datetime import date
from uuid import UUID

from src.common.domain.repository import IRepository
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement
from src.finance.domain.entities.purchases import PurchaseEntity


class IPurchasesRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> PurchaseEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, user_id: UUID) -> list[PurchaseEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        supplie_id: UUID,
        amount: float,
        price: float,
        purchase_date: date,
        unit_price: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        amount: float,
        price: float,
        purchase_date: date,
        unit_price: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
