from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class SaleEntity:
    id: UUID
    tenant_id: UUID
    sale_date: date
    price: Decimal
    price_per_kg: Decimal
    weight: float
    description: str = field(default_factory=str)

    buyer_id: UUID | None = None
    animal_id: UUID | None = None
    created_at: datetime | None = None
