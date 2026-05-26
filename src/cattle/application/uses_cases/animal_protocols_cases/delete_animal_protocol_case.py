from uuid import UUID

from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.services.animal_protocols.delete_animal_protocol_service import DeleteAnimalProtocolService
from src.common.application.ports.uow import IUoW


class DeleteAnimalProtocolCase:
    def __init__(
        self,
        uow: IUoW,
        service: DeleteAnimalProtocolService,
    ):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalProtocolsRepository)
            await self.service.validate_can_delete(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            await self.service.delete_protocol(id, repository)
            await uow.commit()
