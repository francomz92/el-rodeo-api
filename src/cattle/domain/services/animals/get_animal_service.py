from uuid import UUID

from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.common.domain.exceptions import NotFoundError


class GetAnimalService:
    async def validate_existence_and_get_animal(self, id: UUID, user_id: UUID, repository: IAnimalsRepository) -> AnimalEntity:
        animal = await repository.get_by_id(id=id, user_id=user_id)
        if not animal:
            raise NotFoundError("El animal que intenta ver no se encuentra registrado")
        return animal
