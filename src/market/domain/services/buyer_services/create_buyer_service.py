from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositoriyes.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import BuyerCreateValueObject


class CreateBuyerService:
    async def create_new(
        self,
        data: BuyerCreateValueObject,
        repository: IBuyersRepository,
    ) -> BuyerEntity:
        return await repository.create(data)
