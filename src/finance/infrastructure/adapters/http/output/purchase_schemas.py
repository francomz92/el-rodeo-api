from datetime import date
from uuid import UUID

from pydantic import BaseModel

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.infrastructure.adapters.http.output.animal_supplies_schemas import AnimalSupplySchema


class PurchaseSchema(BaseModel):
    id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
    supply: AnimalSupplySchema
