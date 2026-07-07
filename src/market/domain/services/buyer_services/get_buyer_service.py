from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository


class GetBuyerService:
    async def get_buyer(
        self,
        id: UUID,
        repository: IBuyersRepository,
    ) -> BuyerEntity:
        buyer = await repository.get_by_id(id)
        if buyer is None:
            raise NotFoundError("No se encontró el comprador seleccionado.")
        return buyer
