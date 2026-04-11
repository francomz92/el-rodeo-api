from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.cattle.domain.constants.animal import AnimalStatus


@dataclass
class AnimalTypeEntinty:
    id: UUID
    name: str


@dataclass
class AnimalEntity:
    id: UUID
    user_id: UUID
    type_id: UUID
    name: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    breed: str
    status: AnimalStatus

    user: UserEntity | None
    type: AnimalTypeEntinty | None

    def validate_initial_weight_date(self):
        if self.initial_weight_date < self.date_of_birth:
            raise ValueError("The date of the initial weighing must not be earlier than the date of birth")
