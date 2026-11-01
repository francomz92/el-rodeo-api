from uuid import UUID

from src.common.domain.exceptions import ConflictError, NotFoundError
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objects.purchase_value_objects import PurchaseListQueryParamValueObject


class DeleteAnimalSuppliesService:
    async def validate_delete(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
        purchase_repository: IPurchasesRepository,
    ) -> None:
        supply = await repository.get_by_id(id=id)
        if not supply:
            raise NotFoundError("Insumo no encontrado")
        # list_for_user returns (items, total, has_next); only the items
        # decide whether the supply has purchases.
        related_purchases, _total, _has_next = await purchase_repository.list_for_user(
            filters=PurchaseListQueryParamValueObject(supply_id=id),
            limit=1,
            offset=0,
            order_by="id",
        )
        if related_purchases:
            raise ConflictError("El insumo no puede ser eliminado porque tiene compras asociadas")

    async def delete_supply(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        await repository.delete(id=id)
