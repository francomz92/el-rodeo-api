from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
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
            await self.service.validate_supply_exists(
                user_id=data.user_id,
                supply_id=data.supply_id,
                supply_repository=supply_repository,
            )
            repository = uow.get_repository(IPurchasesRepository)
            purchase = await self.service.create_new(data.user_id, data, repository)
            await self.service.increase_supply_stock(
                supply_id=data.supply_id,
                amount_to_increase=data.amount,
                supply_repository=supply_repository,
            )
            await uow.commit()
            return purchase
