from uuid import UUID

from src.cattle.domain.events.animal_events import AnimalUpdated
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.update_animal_service import UpdateAnimalService
from src.cattle.domain.value_objects.animal_value_object import AnimalUpdateValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus


class UpdateAnimalCase:
    def __init__(self, uow: IUoW, service: UpdateAnimalService, event_bus: IEventBus) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, id: UUID, data: AnimalUpdateValueObject):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            await self.service.validate_existence(
                id=id,
                repository=repository,
            )
            animal = await self.service.update_animal(
                id=id,
                data=data,
                repository=repository,
            )
            await uow.commit()

        await self.event_bus.dispatch(AnimalUpdated(aggregate_id=animal.id))
        return animal
