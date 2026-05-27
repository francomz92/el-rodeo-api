from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.common.domain.types import Sentinel
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement


@dataclass
class PurchaseListQueryParamValueObject:
    id: UUID | Sentinel = Sentinel.UNSET
    supply_id: UUID | Sentinel = Sentinel.UNSET
    purchase_date: date | Sentinel = Sentinel.UNSET
    unit_of_measurement: UnitOfMeasurement | Sentinel = Sentinel.UNSET


@dataclass
class PurchaseCreateValueObject:
    user_id: UUID
    supply_id: UUID
    amount: float
    price: float
    purchase_date: date
    unit_price: float
    unit_of_measurement: UnitOfMeasurement
