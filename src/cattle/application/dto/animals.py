from dataclasses import dataclass

from src.cattle.domain.entities.animal_entity import AnimalEntity


@dataclass
class ListAnimalsResult:
    items: list[AnimalEntity]
    total: int
    has_next: bool
