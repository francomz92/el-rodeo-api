from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.common.application.types import Sentinel


@dataclass
class AnimalProtocolListQueryParamsValueObject:
    animal_id: UUID | Sentinel = Sentinel.UNSET
    vaccinated: bool | Sentinel = Sentinel.UNSET
    sale_permission: bool | Sentinel = Sentinel.UNSET


@dataclass
class AnimalProtocolCreateValueObject:
    animal_id: UUID
    vaccinated: bool = False
    vaccinated_date: date | None = None
    sale_permission: bool = False
    sale_permission_date: date | None = None


@dataclass
class AnimalProtocolUpdateValueObject:
    user_id: UUID
    vaccinated: bool
    vaccinated_date: date | None
    sale_permission: bool
    sale_permission_date: date | None
