from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.market.domain.entities.buyers import BuyerEntity


class IBuyersRepository(IRepository):
    @abstractmethod
    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> BuyerEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, user_id: UUID) -> list[BuyerEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        name: str,
        description: str,
        contact_number: str,
        contact_address: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        description: str,
        contact_number: str,
        contact_address: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
