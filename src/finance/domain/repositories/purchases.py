from abc import abstractmethod
from datetime import date
from uuid import UUID

from src.common.domain.repository import IRepository
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.value_objects.purchase_value_objects import PurchaseCreateValueObject, PurchaseListQueryParamValueObject


class IPurchasesRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> PurchaseEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[PurchaseEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        data: PurchaseCreateValueObject,
    ) -> PurchaseEntity:
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
