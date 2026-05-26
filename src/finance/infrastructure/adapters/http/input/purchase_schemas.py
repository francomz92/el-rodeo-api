from datetime import date
from uuid import UUID

from pydantic import BaseModel

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement


class PurchaseListQueryParamsSchema(StandardQueryParams):
    id: UUID | None = None
    purchase_date: date | None = None
    unit_of_measurement: UnitOfMeasurement | None = None
    supply_id: UUID | None = None


class PurchaseCreateSchema(BaseModel):
    supply_id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
