from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement


@dataclass
class SuplyTypeEntinty:
    id: UUID
    name: str


@dataclass
class AnimalSupplieEntity:
    id: UUID
    user_id: UUID
    type_id: UUID
    created_at: datetime
    name: str
    amount: float
    critical_amount: float
    unit_of_measurement: UnitOfMeasurement
    description: str = field(default_factory=str)

    user: UserEntity | None = None
    type: SuplyTypeEntinty | None = None

    def validate_critical_amount(self):
        if self.critical_amount < self.amount:
            raise ValueError("Critical amount must be higher than amount de supplies")
