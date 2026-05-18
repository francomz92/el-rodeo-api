from uuid import UUID
from datetime import date
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement
from src.finance.infrastructure.adapters.http.output.animal_supplies_schemas import AnimalSupplySchema
from pydantic import BaseModel


class PurchaseSchema(BaseModel):
    id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
    supplie: AnimalSupplySchema
