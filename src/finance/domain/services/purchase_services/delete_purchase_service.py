from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.repositories.purchases import IPurchasesRepository


class DeletePurchaseService:
    async def validate_existence(
        self,
        id: UUID,
        repository: IPurchasesRepository,
    ):
        purchase = await repository.get_by_id(id=id)
        if not purchase:
            raise NotFoundError("Compra no encontrada")

    async def delete_purchase(
        self,
        id: UUID,
        repository: IPurchasesRepository,
    ):
        await repository.delete(id=id)
