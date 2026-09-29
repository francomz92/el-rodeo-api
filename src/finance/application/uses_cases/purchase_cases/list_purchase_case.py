from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.repositories.user_reader_port import IUserNameReader
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
            purchases = await self.service.get_purchases(
                repository=repository,
                query=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )
            if purchases:
                linked_user_ids: set[UUID] = {purchase.user_id for purchase in purchases if purchase.user_id is not None}
                user_names: dict[UUID, str] = {}
                if linked_user_ids:
                    user_reader = uow.get_repository(IUserNameReader)
                    user_names = await user_reader.get_names_by_ids(linked_user_ids)
                for purchase in purchases:
                    purchase.user_name = user_names.get(purchase.user_id) if purchase.user_id is not None else None
            return purchases
