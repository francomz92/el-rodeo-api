from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.cattle.infrastructure.adapters.http.output.animal_schemas import AnimalSchema


class AnimalProtocolSchema(BaseModel):
    id: UUID
    animal: AnimalSchema
    vaccinated: bool
    vaccinated_date: date | None
    sale_permission: bool
    sale_permission_date: date | None

    model_config = ConfigDict(from_attributes=True)
