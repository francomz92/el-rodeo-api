from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import BuyerUpdateValueObject


class UpdateBuyerService:
    async def validate_buyer_exists(
        self,
        id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        buyer = await repository.get_by_id(id)
        if not buyer:
            raise NotFoundError("El comprador que intenta actualizar no existe.")

    async def update_buyer(
        self,
        id: UUID,
        data: BuyerUpdateValueObject,
        repository: IBuyersRepository,
    ) -> BuyerEntity:
        return await repository.update_data(id, data)
