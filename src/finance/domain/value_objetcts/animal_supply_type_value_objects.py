from dataclasses import dataclass

from src.common.domain.types import Sentinel


@dataclass
class AnimalSupplyTypeListQueryParamsValueObject:
    name: str | Sentinel = Sentinel.UNSET


@dataclass
class AnimalSupplyTypeCreateValueObject:
    name: str


@dataclass
class AnimalSupplyTypeUpdateValueObject:
    name: str
