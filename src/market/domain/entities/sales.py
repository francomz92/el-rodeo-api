from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.market.domain.entities.buyers import BuyerEntity


@dataclass
class SaleEntity:
    id: UUID
    sale_date: date
    price: float
    price_per_kg: float
    weight: float
    description: str = field(default_factory=str)

    user: UserEntity | None = None
    buyer: BuyerEntity | None = None
    animal: AnimalEntity | None = None

    def validate_price_per_kg(self):
        if self.price_per_kg < self.price:
            raise ValueError("El precio por kilo no puede ser inferior al precio de venta")
