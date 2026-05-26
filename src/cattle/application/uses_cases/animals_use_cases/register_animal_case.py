from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.services.animal_protocols.create_animal_protocol_service import CreateAnimalProtocolService
from src.cattle.domain.services.animals.register_animal_service import RegisterAnimalService
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolCreateValueObject
from src.cattle.domain.value_objects.animal_value_objenct import AnimalCreateValueObject
from src.common.application.ports.uow import IUoW


class RegisterAnimalCase:
    async def __init__(
        self,
        uow: IUoW,
        service: RegisterAnimalService,
        create_animal_protocol_service: CreateAnimalProtocolService,
    ) -> None:
        self.uow = uow
        self.service = service
        self.animal_protocol_service = create_animal_protocol_service

    async def execute(self, data: AnimalCreateValueObject):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            type_repository = uow.get_repository(IAnimalTypesRepository)
            protocol_repository = uow.get_repository(IAnimalProtocolsRepository)
            await self.service.validate_duplicate(
                user_id=data.user_id,
                type_id=data.type_id,
                caravana=data.caravana,
                repository=repository,
            )
            await self.service.validate_type_exists(
                type_id=data.type_id,
                repository=type_repository,
            )
            animal = await self.service.create_new(
                data=data,
                repository=repository,
            )
            await self.animal_protocol_service.create_new(
                user_id=data.user_id,
                data=AnimalProtocolCreateValueObject(animal_id=animal.id),
                repository=protocol_repository,
            )
            await uow.commit()
        return animal
