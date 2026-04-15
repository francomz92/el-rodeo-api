from abc import abstractmethod
from datetime import date
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal import AnimalEntity
from src.common.application.ports.repository import IRepository


class IAnimalsRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID | None) -> AnimalEntity | None:
        raise NotImplemented
    
    @abstractmethod
    async def get_by_caravana(self, caravana: str) -> AnimalEntity | None:
        raise NotImplemented

    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[AnimalEntity]:
        raise NotImplemented

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        animal_type_id: UUID,
        caravana: str,
        name: str,
        date_of_birth: date,
        initial_weight: float,
        initial_weight_date: date,
        last_weight: float,
        breed: str,
        tag: str,
        status: AnimalStatus,
    ) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        caravana: str,
        name: str,
        date_of_birth: date,
        initial_weight: float,
        initial_weight_date: date,
        last_weight: float,
        breed: str,
    ) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_status(self, id: UUID, status: AnimalStatus) -> None:
        raise NotImplemented

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplemented
