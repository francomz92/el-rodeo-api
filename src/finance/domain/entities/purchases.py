from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.domain.constants.purchases import PurchaseStatus


@dataclass
class PurchaseEntity:
    id: UUID
    tenant_id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
    user_id: UUID | None
    user_name: str | None
    supply_id: UUID
    supply_name: str
    status: PurchaseStatus = PurchaseStatus.PENDING
    confirmed_at: datetime | None = None
    confirmed_by: UUID | None = None

    def validate_unit_price(self):
        if self.unit_price < 0:
            raise ValueError("El precio de compra no puede ser negativo")
        if abs(self.unit_price * self.amount - self.price) > 0.01:
            raise ValueError("El precio unitario por la cantidad no coincide con el precio de compra")
