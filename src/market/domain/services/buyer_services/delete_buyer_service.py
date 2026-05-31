from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositories.buyers import IBuyersRepository


class DeleteBuyerService:
    async def validate_buyer_exists(
        self,
        id: UUID,
        user_id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        buyer_exists = await repository.exists(id, user_id)
        if not buyer_exists:
            raise NotFoundError("El comprador que intenta eliminar no existe.")

    async def delete_buyer(
        self,
        id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        await repository.delete(id)
