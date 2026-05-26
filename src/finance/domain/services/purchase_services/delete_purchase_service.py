from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.repositories.purchases import IPurchasesRepository


class DeletePurchaseService:
    async def validate_purchase_exists(
        self,
        id: UUID,
        user_id: UUID,
        repository: IPurchasesRepository,
    ) -> None:
        purchase_exists = await repository.exists(id, user_id)
        if not purchase_exists:
            raise NotFoundError("La compra que intenta eliminar no existe.")

    async def delete_purchase(
        self,
        id: UUID,
        user_id: UUID,
        repository: IPurchasesRepository,
    ) -> None:
        await repository.delete(id)
