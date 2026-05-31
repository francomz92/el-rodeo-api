from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import BuyerUpdateValueObject


class UpdateBuyerService:
    async def validate_buyer_exists(
        self,
        id: UUID,
        user_id: UUID,
        repository: IBuyersRepository,
    ) -> None:
        buyer_exists = await repository.exists(id, user_id)
        if not buyer_exists:
            raise NotFoundError("El comprador que intenta actualizar no existe.")

    async def update_buyer(
        self,
        id: UUID,
        user_id: UUID,
        data: BuyerUpdateValueObject,
        repository: IBuyersRepository,
    ) -> BuyerEntity:
        return await repository.update_data(id, user_id, data)
