from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from src.common.domain.types import Sentinel


@dataclass
class SaleListQueryParamsValueObject:
    sale_date: date | Sentinel = Sentinel.UNSET
    price: str | Sentinel = Sentinel.UNSET
    buyer_id: UUID | Sentinel = Sentinel.UNSET


@dataclass
class SaleCreateValueObject:
    user_id: UUID
    animal_id: UUID
    buyer_id: UUID
    sale_date: date
    price: float
    price_per_kg: float
    weight: float
    description: str = field(default_factory=str)
