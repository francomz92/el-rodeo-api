from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.cattle.domain.value_objects.animal_value_object import (
    AnimalCreateValueObject,
    AnimalsListQueryParamsValueObject,
    AnimalUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IAnimalsRepository(IRepository):
    @abstractmethod
    async def exists(
        self,
        id: UUID | None = None,
        type_id: UUID | None = None,
        caravana: str | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID, lock: bool = False) -> AnimalEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_caravana(self, caravana: str) -> AnimalEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        filters: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> tuple[list[AnimalEntity], int, bool]:
        """List animals matching filters with pagination.

        When *cursor* is provided, cursor-based pagination is used
        (``WHERE id > :cursor_id ORDER BY id ASC``) and offset is ignored.
        When *cursor* is ``None``, the legacy offset/limit pagination is used.

        Returns ``(items, total_count, has_next)``.
        ``has_next`` is ``True`` when there are more items after the returned page
        (cursor mode only; always ``False`` when cursor is ``None``).
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: AnimalCreateValueObject) -> AnimalEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: AnimalUpdateValueObject) -> AnimalEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, id: UUID, status: AnimalStatus) -> None:
        # TODO: unused — remove if no caller emerges after refactoring
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
