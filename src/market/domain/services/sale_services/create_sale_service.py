from src.common.domain.exceptions import BusinessValidationError
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositoriyes.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject


class CreateSaleService:
    def validate_data(self, data: SaleCreateValueObject) -> None:
        if data.price_per_kg > data.price:
            raise BusinessValidationError(
                message="Los precios son inconsistentes.",
                details=[{"field": "price_per_kg", "message": "El precio por kilogramo no puede ser mayor que el precio total."}],
            )

    async def create_new(
        self,
        data: SaleCreateValueObject,
        repository: ISalesRepository,
    ) -> SaleEntity:
        return await repository.create(data)
