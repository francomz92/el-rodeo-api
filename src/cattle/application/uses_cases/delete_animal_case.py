from uuid import UUID

from src.cattle.application.ports.repositories.animals_repository_port import IAnimalsRepository
from src.common.application.exceptions import ConflictError, ResourceNotFoundError
from src.common.application.ports.uow import IUoW


class DeleteAnimalCase:
    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, id: UUID, user_id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            animal = await repository.get_by_id(id, user_id)
            if not animal:
                raise ResourceNotFoundError(f"El registro que intenta eliminar no existe")
            if not animal.can_delete():
                raise ConflictError("No se puede eliminar porque se encuntra vendido")
            await repository.delete(id)
            await uow.commit()
