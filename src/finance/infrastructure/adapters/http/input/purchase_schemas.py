from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


class PurchaseListQueryParamsSchema(StandardQueryParams):
    id: UUID | None = None
    purchase_date: date | None = None
    unit_of_measurement: UnitOfMeasurement | None = None
    supply_id: UUID | None = None


class PurchaseCreateSchema(BaseModel):
    supply_id: UUID
    amount: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    purchase_date: date
    unit_price: float = Field(..., gt=0)
    unit_of_measurement: UnitOfMeasurement
