from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class SaleListQueryParamsSchema(StandardQueryParams):
    ALLOWED_ORDER_BY: frozenset[str] = frozenset({"sale_date", "price", "weight", "created_at"})

    buyer_id: UUID | None = None
    sale_date: date | None = None
    price: Decimal | None = None


class SaleCreateSchema(BaseModel):
    animal_id: UUID
    buyer_id: UUID
    sale_date: date
    price: Decimal = Field(..., gt=0)
    price_per_kg: Decimal = Field(..., gt=0)
    weight: float = Field(..., gt=0)
    description: str = Field("", max_length=500)


class SaleUpdateSchema(BaseModel):
    price: Decimal | None = Field(None, gt=0)
    price_per_kg: Decimal | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=500)
    buyer_id: UUID | None = None
    animal_id: UUID | None = None
    sale_date: date | None = None
