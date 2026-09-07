from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


@dataclass
class PurchaseEntity:
    id: UUID
    tenant_id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
    user_id: UUID
    user_name: str
    supply_id: UUID
    supply_name: str

    def validate_unit_price(self):
        if self.unit_price < 0:
            raise ValueError("Purchase price cant be negative")
        if abs(self.unit_price * self.amount - self.price) > 0.01:
            raise ValueError("El precio unitario por la cantidad no coincide con el precio de compra")
