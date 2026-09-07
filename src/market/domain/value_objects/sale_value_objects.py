from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.common.domain.types import Sentinel


@dataclass
class SaleListQueryParamsValueObject:
    buyer_id: UUID | Sentinel = Sentinel.UNSET
    sale_date: date | Sentinel = Sentinel.UNSET
    price: Decimal | Sentinel = Sentinel.UNSET


@dataclass
class SaleCreateValueObject:
    user_id: UUID
    animal_id: UUID
    buyer_id: UUID
    sale_date: date
    price: Decimal
    price_per_kg: Decimal
    weight: float
    description: str = field(default_factory=str)


@dataclass
class SaleUpdateValueObject:
    buyer_id: UUID | Sentinel = Sentinel.UNSET
    animal_id: UUID | Sentinel = Sentinel.UNSET
    sale_date: date | Sentinel = Sentinel.UNSET
    price: Decimal | Sentinel = Sentinel.UNSET
    price_per_kg: Decimal | Sentinel = Sentinel.UNSET
    weight: float | Sentinel = Sentinel.UNSET
    description: str | Sentinel = Sentinel.UNSET
