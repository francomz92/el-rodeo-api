from datetime import date
from uuid import UUID

from pydantic import BaseModel

from src.cattle.infrastructure.adapters.http.output.animal_types import AnimalTypeSchema


class AnimalSchema(BaseModel):
    id: UUID
    type: AnimalTypeSchema
    caravana: str
    name: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    breed: str
    status: str
