from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class SaleListQueryParamsSchema(StandardQueryParams):
    buyer_id: UUID | None = None
    sale_date: date | None = None
    price: float | None = None


class SaleCreateSchema(BaseModel):
    animal_id: UUID
    buyer_id: UUID
    sale_date: date
    price: float
    price_per_kg: float
    weight: float
    description: str = Field("", max_length=500)
