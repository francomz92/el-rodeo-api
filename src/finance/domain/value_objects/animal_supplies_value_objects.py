from dataclasses import dataclass
from uuid import UUID

from src.common.domain.types import Sentinel
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


@dataclass
class AnimalSuppliesListQueryParamsValueObject:
    id: UUID | Sentinel = Sentinel.UNSET
    type_id: UUID | Sentinel = Sentinel.UNSET
    name: str | Sentinel = Sentinel.UNSET


@dataclass
class AnimalSuppliesCreateValueObject:
    type_id: UUID
    user_id: UUID
    name: str
    amount: float
    critical_amount: float
    unit_of_measurement: UnitOfMeasurement
    description: str = ""


@dataclass
class AnimalSuppliesUpdateValueObject:
    type_id: UUID
    name: str
    amount: float
    critical_amount: float
    unit_of_measurement: UnitOfMeasurement
    description: str | Sentinel = Sentinel.UNSET
