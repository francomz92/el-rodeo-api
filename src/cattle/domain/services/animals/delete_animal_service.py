from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.common.domain.exceptions import ConflictError, NotFoundError


class DeleteAnimalService:
    async def validate_animal_for_delete(
        self,
        id: UUID,
        user_id: UUID,
        repository: IAnimalsRepository,
    ):
        animal = await repository.get_by_id(id=id, user_id=user_id)
        if not animal:
            raise NotFoundError("El animal que intenta eliminar no existe")
        if not animal.can_delete():
            raise ConflictError("No se puede eliminar porque se encuntra vendido")

    async def delete_animal(self, id: UUID, repository: IAnimalsRepository):
        await repository.delete(id=id)
