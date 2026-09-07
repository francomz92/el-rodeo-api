from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus

# TODO: move AnimalTypeEntity to its own module: src/cattle/domain/entities/animal_type_entity.py


@dataclass
class AnimalTypeEntity:
    id: UUID
    name: str


@dataclass
class AnimalEntity:
    id: UUID
    tenant_id: UUID
    caravana: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    breed: str
    status: AnimalStatus

    user_id: UUID | None = None
    type: AnimalTypeEntity | None = None

    def validate_initial_weight_date(self):
        if self.initial_weight_date < self.date_of_birth:
            raise ValueError("La fecha del pesaje inicial no debe ser anterior a la fecha de nacimiento")

    # TODO: wire this validation into the registration flow

    def can_update(self) -> bool:
        return self.status != AnimalStatus.SOLD

    def can_delete(self) -> bool:
        return self.status != AnimalStatus.SOLD
