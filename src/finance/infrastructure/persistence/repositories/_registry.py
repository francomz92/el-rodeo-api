from src.common.domain.repository import IRepository
from src.finance.domain.repositories.gdpr_data_repository_port import (
    IFinanceGDPRDataRepository,
)
from src.finance.infrastructure.persistence.repositories.animal_supplies import (
    AnimalSuppliesRepository,
    IAnimalSuppliesRepository,
)
from src.finance.infrastructure.persistence.repositories.animal_supply_types import (
    ISupplyTypesRepository,
    SupplyTypesRepository,
)
from src.finance.infrastructure.persistence.repositories.gdpr_data_repository import (
    FinanceGDPRDataRepository,
)
from src.finance.infrastructure.persistence.repositories.purchases import (
    IPurchasesRepository,
    PurchasesRepository,
)

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IAnimalSuppliesRepository: AnimalSuppliesRepository,
    ISupplyTypesRepository: SupplyTypesRepository,
    IPurchasesRepository: PurchasesRepository,
    IFinanceGDPRDataRepository: FinanceGDPRDataRepository,
}
