from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.services.animal_protocols.update_animal_protocol_service import UpdateAnimalProtocolService
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolUpdateValueObject
from src.common.application.ports.uow import IUoW


class UpdateAnimalProtocolCase:
    def __init__(
        self,
        uow: IUoW,
        service: UpdateAnimalProtocolService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        animal_id: UUID,
        id: UUID,
        data: AnimalProtocolUpdateValueObject,
    ) -> AnimalProtocolEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalProtocolsRepository)
            animal_repo = uow.get_repository(IAnimalsRepository)
            await self.service.run_validations(id, data, repository)
            protocol = await self.service.update_protocols(animal_id, id, data, repository)
            if protocol.can_be_sold():
                await animal_repo.update_status(animal_id, AnimalStatus.READY)
            else:
                await animal_repo.update_status(animal_id, AnimalStatus.NOT_READY)
            await uow.commit()
            return protocol
