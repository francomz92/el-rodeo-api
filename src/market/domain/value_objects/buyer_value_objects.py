from dataclasses import dataclass, field
from uuid import UUID

from src.common.domain.types import Sentinel


@dataclass
class BuyerListQueryParamsValueObject:
    name: str | Sentinel = Sentinel.UNSET
    contact_number: str | Sentinel = Sentinel.UNSET


@dataclass
class BuyerCreateValueObject:
    user_id: UUID
    name: str
    description: str = field(default_factory=str)
    contact_number: str = field(default_factory=str)
    contact_address: str = field(default_factory=str)


@dataclass
class BuyerUpdateValueObject:
    name: str | Sentinel = Sentinel.UNSET
    description: str | Sentinel = Sentinel.UNSET
    contact_number: str | Sentinel = Sentinel.UNSET
    contact_address: str | Sentinel = Sentinel.UNSET
