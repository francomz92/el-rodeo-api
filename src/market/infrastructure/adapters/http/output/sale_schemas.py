from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SaleSchema(BaseModel):
    id: UUID
    sale_date: date
    price: Decimal
    price_per_kg: Decimal
    weight: float
    description: str

    buyer_id: UUID | None = None
    animal_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)
