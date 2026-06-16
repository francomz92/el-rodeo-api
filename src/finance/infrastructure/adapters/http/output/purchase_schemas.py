from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


class PurchaseSchema(BaseModel):
    id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
    user_id: UUID
    user_name: str
    supply_id: UUID
    supply_name: str

    model_config = ConfigDict(from_attributes=True)
