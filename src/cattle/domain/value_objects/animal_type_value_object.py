from dataclasses import dataclass
from uuid import UUID

from src.common.domain.types import Sentinel


@dataclass
class AnimalTypeListQueryParamsValueObject:
    id: UUID | Sentinel = Sentinel.UNSET
    name: str | Sentinel = Sentinel.UNSET


@dataclass
class AnimalTypeCreateValueObject:
    name: str


@dataclass
class AnimalTypeUpdateValueObject:
    name: str
