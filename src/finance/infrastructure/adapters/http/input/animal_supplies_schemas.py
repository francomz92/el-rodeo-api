from uuid import UUID

from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


class AnimalSuppliesListQueryParamsSchema(StandardQueryParams):
    id: UUID | None = None
    type_id: UUID | None = None
    name: str | None = Field(None, max_length=50)


class AnimalSuppliesCreateSchema(BaseModel):
    type_id: UUID
    name: str
    amount: float
    critical_amount: float
    unit_of_measurement: UnitOfMeasurement
    description: str = ""


class AnimalSuppliesUpdateSchema(BaseModel):
    type_id: UUID
    name: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0)
    critical_amount: float = Field(..., gt=0)
    unit_of_measurement: UnitOfMeasurement
    description: str | None = Field(None, max_length=500)
