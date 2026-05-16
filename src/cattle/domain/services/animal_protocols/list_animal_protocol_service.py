from uuid import UUID

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolListQueryParamsValueObject


class ListAnimalProtocolService:
    async def get_animal_protocols(
        self,
        user_id: UUID,
        repository: IAnimalProtocolsRepository,
        filters: AnimalProtocolListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalProtocolEntity]:
        animal_protocols = await repository.list_for_user(
            user_id,
            filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return animal_protocols
