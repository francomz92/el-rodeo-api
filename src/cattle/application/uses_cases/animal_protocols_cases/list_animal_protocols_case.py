from uuid import UUID

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.services.animal_protocols.list_animal_protocol_service import ListAnimalProtocolService
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolListQueryParamsValueObject
from src.common.application.ports.uow import IUoW


class ListAnimalProtocolsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListAnimalProtocolService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        query_params: AnimalProtocolListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalProtocolEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalProtocolsRepository)
            protocols = await self.service.get_animal_protocols(
                user_id,
                repository,
                query_params,
                limit,
                offset,
                order_by,
            )
            return protocols
