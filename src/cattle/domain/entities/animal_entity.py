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
    caravana: str
    name: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    breed: str
    status: AnimalStatus

    user: UserEntity | None = None
    type: AnimalTypeEntinty | None = None

    def validate_initial_weight_date(self):
        if self.initial_weight_date < self.date_of_birth:
            raise ValueError("La fecha del pesaje inicial no debe ser anterior a la fecha de nacimiento")

    def can_update(self):
        return self.status != AnimalStatus.SOLD

    def can_delete(self) -> bool:
        return self.status != AnimalStatus.SOLD
