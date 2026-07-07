from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositories.buyers import IBuyersRepository


class DeleteBuyerService:
    async def validate_buyer_exists(
        self,
        id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        buyer = await repository.get_by_id(id)
        if not buyer:
            raise NotFoundError("El comprador que intenta eliminar no existe.")

    async def delete_buyer(
        self,
        id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        await repository.delete(id)
