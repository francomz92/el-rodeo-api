from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.finance.domain.entities.animal_supplies import AnimalSupplieEntity, UnitOfMeasurement


@dataclass
class PurchaseEntity:
    id: UUID
    supplie_id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement

    user: UserEntity | None = None
    supplie: AnimalSupplieEntity | None = None

    def validate_unit_price(self):
        if self.unit_price < 0:
            raise ValueError("Purchase price cant be negative")
        if self.unit_price > self.price:
            raise ValueError("Unit price cant be higher than purchase price")
