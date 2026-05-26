from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.value_objects.animal_protocol_value_object import (
    AnimalProtocolCreateValueObject,
    AnimalProtocolListQueryParamsValueObject,
    AnimalProtocolUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IAnimalProtocolsRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> AnimalProtocolEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalProtocolListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalProtocolEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        data: AnimalProtocolCreateValueObject,
    ) -> AnimalProtocolEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        data: AnimalProtocolUpdateValueObject,
    ) -> AnimalProtocolEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
