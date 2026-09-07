from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositories.buyers import IBuyersRepository


class DeleteBuyerService:
    async def delete_buyer(
        self,
        id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        deleted = await repository.delete(id)
        if not deleted:
            raise NotFoundError("El comprador que intenta eliminar no existe.")
