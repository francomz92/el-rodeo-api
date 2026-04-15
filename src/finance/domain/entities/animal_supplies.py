from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.common.utils.date_utils import get_current_datetime
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement


@dataclass
class SupplyTypeEntinty:
    id: UUID
    name: str


@dataclass
class AnimalSupplyEntity:
    id: UUID
    name: str
    amount: float
    critical_amount: float
    unit_of_measurement: UnitOfMeasurement
    created_at: datetime = field(default_factory=get_current_datetime)
    description: str = field(default_factory=str)

    user: UserEntity | None = None
    type: SupplyTypeEntinty | None = None

    def validate_critical_amount(self):
        if self.critical_amount < self.amount:
            raise ValueError("La cantidad crítica debe ser superior a la cantidad de existencias")
