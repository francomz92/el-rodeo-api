from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.list_purchase_service import ListPurchaseService
from src.finance.domain.value_objects.purchase_value_objects import PurchaseListQueryParamValueObject


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
        filters: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[PurchaseEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            return await self.service.get_purchases(
                repository=repository,
                query=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )
