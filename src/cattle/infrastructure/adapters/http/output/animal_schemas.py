from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.cattle.infrastructure.adapters.http.output.animal_type_schemas import AnimalTypeSchema


class AnimalSchema(BaseModel):
    id: UUID
    type: AnimalTypeSchema
    caravana: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    breed: str
    status: str

    model_config = ConfigDict(from_attributes=True)
