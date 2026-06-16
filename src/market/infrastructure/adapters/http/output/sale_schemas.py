from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.auth.domain.entities import UserEntity
from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.market.domain.entities.buyers import BuyerEntity


class SaleSchema(BaseModel):
    id: UUID
    sale_date: date
    price: float
    price_per_kg: float
    weight: float
    description: str

    user: UserEntity | None = None
    buyer: BuyerEntity | None = None
    animal: AnimalEntity | None = None

    model_config = ConfigDict(from_attributes=True)
