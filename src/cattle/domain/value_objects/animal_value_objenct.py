from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.domain.types import Sentinel


@dataclass
class AnimalsListQueryParamsValueObject:
    type_id: UUID | None | Sentinel = Sentinel.UNSET
    caravana: str | None | Sentinel = Sentinel.UNSET
    name: str | None | Sentinel = Sentinel.UNSET
    breed: str | None | Sentinel = Sentinel.UNSET


@dataclass
class AnimalCreateValueObject:
    user_id: UUID
    type_id: UUID
    caravana: str
    name: str
    breed: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    status: AnimalStatus = AnimalStatus.NOT_READY


@dataclass
class AnimalUpdateValueObject:
    user_id: UUID
    type_id: UUID
    caravana: str | None | Sentinel = Sentinel.UNSET
    name: str | None | Sentinel = Sentinel.UNSET
    date_of_birth: date | None | Sentinel = Sentinel.UNSET
    initial_weight: float | None | Sentinel = Sentinel.UNSET
    initial_weight_date: date | None | Sentinel = Sentinel.UNSET
    last_weight: float | None | Sentinel = Sentinel.UNSET
    breed: str | None | Sentinel = Sentinel.UNSET
    tag: str | None | Sentinel = Sentinel.UNSET
