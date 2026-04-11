from src.common.application.ports.repository import IRepository
from src.auth.infrastructure.persistance.repositories.users import IUserRepository, UserRepository
from src.cattle.infrastructure.persistance.repositories.animals import IAnimalsRepository, AnimalRepository
from src.cattle.infrastructure.persistance.repositories.animal_types import AnimalTypeRepository, IAnimalTypesRepository
from src.finance.infrastructure.persistance.repositories.animal_suppiles import AnimalSuppliesRepository, IAnimalSuppliesRepository
from src.finance.infrastructure.persistance.repositories.animal_supplie_types import SupplyTypesRepository, ISupplyTypesRepository
from src.market.infrastructure.persistance.repositories.buyers import BuyersRepository, IBuyersRepository
from src.market.infrastructure.persistance.repositories.sales import ISalesRepository, SalesRepository
from src.finance.infrastructure.persistance.repositories.purchases import IPurchasesRepository, PurchasesRepository


repositories_list: dict[type[IRepository], type[IRepository]] = {
    IUserRepository: UserRepository,
    IAnimalsRepository: AnimalRepository,
    IAnimalTypesRepository: AnimalTypeRepository,
    IAnimalSuppliesRepository: AnimalSuppliesRepository,
    ISupplyTypesRepository: SupplyTypesRepository,
    IPurchasesRepository: PurchasesRepository,
    IBuyersRepository: BuyersRepository,
    ISalesRepository: SalesRepository,
}
