from datetime import date
from uuid import UUID

from pydantic import BaseModel

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class AnimalProtocolsListQueryParamsSchema(StandardQueryParams):
    id: UUID | None = None
    animal_id: UUID | None = None
    vaccinated: bool | None = None
    sale_permission: bool | None = None


class AnimalProtocolsCreateSchema(BaseModel):
    animal_id: UUID


class AnimalProtocolsUpdateSchema(BaseModel):
    vaccinated: bool
    vaccinated_date: date | None
    sale_permission: bool
    sale_permission_date: date | None
