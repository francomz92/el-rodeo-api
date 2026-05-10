from uuid import UUID

from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.common.domain.exceptions import NotFoundError, NotPermissionError


class UpdateAnimalService:
    async def validate_existence(self, id: UUID, user_id: UUID, repository: IAnimalsRepository) -> None:
        animal = await repository.get_by_id(id, user_id)
        if not animal:
            raise NotFoundError("El animal que intenta actualizar no existe")
        if not animal.can_delete():
            raise NotPermissionError("No se puede modificar un animal que ya ha sido vendido")

    async def update_animal(self, id: UUID, data, repository: IAnimalsRepository) -> AnimalEntity:
        return await repository.update_data(id=id, data=data)
