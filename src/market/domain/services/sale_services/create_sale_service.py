from decimal import Decimal
from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.repositories.protocol_animals_repository_port import (
    IAnimalProtocolsRepository,
)
from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject


class CreateSaleService:
    def validate_data(self, data: SaleCreateValueObject) -> None:
        if data.price <= 0:
            raise BusinessValidationError(
                message="El precio debe ser mayor a cero.",
                details=[{"field": "price", "message": f"El precio ({data.price}) debe ser positivo."}],
            )
        if data.price_per_kg <= 0:
            raise BusinessValidationError(
                message="El precio por kilo debe ser mayor a cero.",
                details=[{"field": "price_per_kg", "message": f"El precio por kilo ({data.price_per_kg}) debe ser positivo."}],
            )
        if data.weight <= 0:
            raise BusinessValidationError(
                message="El peso debe ser mayor a cero.",
                details=[{"field": "weight", "message": f"El peso ({data.weight}) debe ser positivo."}],
            )

        expected_price = data.price_per_kg * Decimal(str(data.weight))
        diff = abs(expected_price - data.price)
        threshold = max(data.price, Decimal("0.01"))
        if diff / threshold > Decimal("0.1"):
            raise BusinessValidationError(
                message="Los precios son inconsistentes.",
                details=[
                    {
                        "field": "price_per_kg",
                        "message": f"El precio por kilo ({data.price_per_kg}) por el peso ({data.weight}) no coincide con el precio total ({data.price}) dentro del 10% de tolerancia.",
                    }
                ],
            )

    async def validate_eligibility(
        self,
        animal_id: UUID,
        animal_repo: IAnimalsRepository,
        protocol_repo: IAnimalProtocolsRepository,
    ) -> None:
        animal = await animal_repo.get_by_id(animal_id)
        if animal is None:
            raise NotFoundError(message="Animal no encontrado.")

        protocol = await protocol_repo.get_by_animal_id(animal_id)
        if protocol is None:
            raise BusinessValidationError(
                message="El animal no tiene un protocolo registrado.",
                details=[],
            )

        if not protocol.can_be_sold():
            raise BusinessValidationError(
                message="El animal no está habilitado para la venta.",
                details=[
                    {
                        "field": "animal_id",
                        "message": "Verifique el estado, vacunación y permiso de venta del animal.",
                    }
                ],
            )

    async def create_new(
        self,
        data: SaleCreateValueObject,
        repository: ISalesRepository,
        animal_repo: IAnimalsRepository,
        protocol_repo: IAnimalProtocolsRepository,
    ) -> SaleEntity:
        self.validate_data(data)
        await self.validate_eligibility(data.animal_id, animal_repo, protocol_repo)
        return await repository.create(data)
