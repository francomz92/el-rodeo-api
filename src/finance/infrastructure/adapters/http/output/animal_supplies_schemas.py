from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.infrastructure.adapters.http.output.animal_supply_type_schemas import SupplyTypeSchema


class AnimalSupplySchema(BaseModel):
    id: UUID
    name: str
    amount: float
    critical_amount: float
    unit_of_measurement: UnitOfMeasurement
    created_at: datetime
    description: str
    type: SupplyTypeSchema
