from typing import cast

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.repositories.user_reader_port import IUserNameReader
from src.finance.domain.services.purchase_services.create_purchase_service import CreatePurchaseService
from src.finance.domain.value_objects.purchase_value_objects import PurchaseCreateValueObject


class CreatePurchaseCase:
    def __init__(self, uow: IUoW, service: CreatePurchaseService):
        self.uow = uow
        self.service = service

    async def execute(self, data: PurchaseCreateValueObject) -> PurchaseEntity:
        self.service.validate_data(data)
        async with self.uow as uow:
            supply_repository = uow.get_repository(IAnimalSuppliesRepository)
            await self.service.validate_supply(
                supply_id=data.supply_id,
                supply_repository=supply_repository,
            )
            repository = uow.get_repository(IPurchasesRepository)
            purchase = await self.service.create_new_purchase(
                user_id=data.user_id,
                data=data,
                repository=repository,
                supply_repository=supply_repository,
            )
            await supply_repository.increase_stock(
                id=data.supply_id,
                amount_to_increase=data.amount,
            )
            user_reader = uow.get_repository(IUserNameReader)
            user_names = await user_reader.get_names_by_ids({purchase.user_id})
            purchase.user_name = cast(str, user_names.get(purchase.user_id))
            await uow.commit()
            return purchase
