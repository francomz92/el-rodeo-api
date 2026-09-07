from src.common.domain.repository import IRepository
from src.finance.infrastructure.persistence.repositories.animal_supplies import (
    AnimalSuppliesRepository,
    IAnimalSuppliesRepository,
)
from src.finance.infrastructure.persistence.repositories.animal_supply_types import (
    ISupplyTypesRepository,
    SupplyTypesRepository,
)
from src.finance.infrastructure.persistence.repositories.purchases import (
    IPurchasesRepository,
    PurchasesRepository,
)

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IAnimalSuppliesRepository: AnimalSuppliesRepository,
    ISupplyTypesRepository: SupplyTypesRepository,
    IPurchasesRepository: PurchasesRepository,
}
