from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.application.types import UNSET


@dataclass
class AnimalCreateDTO:
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
class AnimalUpdateDTO:
    user_id: UUID
    type_id: UUID
    caravana: str | None | type[UNSET] = UNSET
    name: str | None | type[UNSET] = UNSET
    date_of_birth: date | None | type[UNSET] = UNSET
    initial_weight: float | None | type[UNSET] = UNSET
    initial_weight_date: date | None | type[UNSET] = UNSET
    last_weight: float | None | type[UNSET] = UNSET
    breed: str | None | type[UNSET] = UNSET
    tag: str | None | type[UNSET] = UNSET


@dataclass
class AnimalIdentifierDTO:
    user_id: UUID
    type_id: UUID
    caravana: str