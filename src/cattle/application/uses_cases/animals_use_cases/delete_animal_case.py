from uuid import UUID

from src.cattle.domain.events.animal_events import AnimalDeleted
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus


class DeleteAnimalCase:
    def __init__(self, uow: IUoW, service: DeleteAnimalService, event_bus: IEventBus) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            await self.service.validate_animal_for_delete(
                id=id,
                repository=repository,
            )
            await self.service.delete_animal(
                id=id,
                repository=repository,
            )
            await uow.commit()

        await self.event_bus.dispatch(AnimalDeleted(aggregate_id=id))
