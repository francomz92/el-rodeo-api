from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.list_purchase_service import ListPurchaseService
from src.finance.domain.value_objetcts.purchase_value_objects import PurchaseListQueryParamValueObject


class ListPurchaseCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListPurchaseService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        filter: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[PurchaseEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            return await self.service.list_purchases(
                user_id=user_id,
                filters=filter,
                limit=limit,
                offset=offset,
                order_by=order_by,
                repository=repository,
            )
