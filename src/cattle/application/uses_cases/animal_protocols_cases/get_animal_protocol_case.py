from uuid import UUID

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.services.animal_protocols.get_animal_protocol_service import GetAnimalProtocolService
from src.common.application.ports.uow import IUoW


class GetAnimalProtocolCase:
    def __init__(
        self,
        uow: IUoW,
        service: GetAnimalProtocolService,
    ):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> AnimalProtocolEntity:
        async with self.uow as uow:
            respository = uow.get_repository(IAnimalProtocolsRepository)
            return await self.service.get_animal_protocol(
                id,
                user_id,
                respository,
            )
