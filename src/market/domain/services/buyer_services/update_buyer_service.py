from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.common.domain.types import Sentinel
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import BuyerUpdateValueObject


class UpdateBuyerService:
    async def update_buyer(
        self,
        id: UUID,
        data: BuyerUpdateValueObject,
        repository: IBuyersRepository,
    ) -> BuyerEntity:
        if all(v is Sentinel.UNSET for v in vars(data).values()):
            raise BusinessValidationError(
                message="No hay campos para actualizar.",
                details=[{"field": "data", "message": "Debe especificar al menos un campo para actualizar."}],
            )
        result = await repository.update_data(id, data)
        if result is None:
            raise NotFoundError("El comprador que intenta actualizar no existe.")
        return result
