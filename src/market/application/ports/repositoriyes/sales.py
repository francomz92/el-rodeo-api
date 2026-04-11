from abc import abstractmethod
from datetime import date
from uuid import UUID

from src.common.application.ports.repository import IRepository
from src.market.domain.entities.sales import SaleEntity


class ISalesRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> SaleEntity | None:
        raise NotImplemented

    @abstractmethod
    async def list_all(self, user_id: UUID) -> list[SaleEntity]:
        raise NotImplemented

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        buyer_id: UUID,
        animal_id: UUID,
        sale_date: date,
        price: float,
        price_per_kg: float,
        weight: float,
        description: str,
    ) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        buyer_id: UUID,
        animal_id: UUID,
        sale_date: date,
        price: float,
        price_per_kg: float,
        weight: float,
        description: str,
    ) -> None:
        raise NotImplemented

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplemented
