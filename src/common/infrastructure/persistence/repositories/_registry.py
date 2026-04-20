from src.common.application.ports.repository import IRepository
from src.auth.infrastructure.persistance.repositories.user_repository import IUserRepository, UserRepository
from src.cattle.infrastructure.persistance.repositories.schedule_event_repository import IScheduleEventRepository, ScheduleEventRepository
from src.cattle.infrastructure.persistance.repositories.animal_repository import IAnimalsRepository, AnimalRepository
from src.cattle.infrastructure.persistance.repositories.animal_type_repository import AnimalTypeRepository, IAnimalTypesRepository
from src.finance.infrastructure.persistance.repositories.animal_suppiles import AnimalSuppliesRepository, IAnimalSuppliesRepository
from src.finance.infrastructure.persistance.repositories.animal_supplie_types import SupplyTypesRepository, ISupplyTypesRepository
from src.finance.infrastructure.persistance.repositories.purchases import IPurchasesRepository, PurchasesRepository
from src.market.infrastructure.persistance.repositories.buyers import BuyersRepository, IBuyersRepository
from src.market.infrastructure.persistance.repositories.sales import ISalesRepository, SalesRepository


repositories_list: dict[type[IRepository], type[IRepository]] = {
    IUserRepository: UserRepository,
    IAnimalsRepository: AnimalRepository,
    IAnimalTypesRepository: AnimalTypeRepository,
    IAnimalSuppliesRepository: AnimalSuppliesRepository,
    ISupplyTypesRepository: SupplyTypesRepository,
    IPurchasesRepository: PurchasesRepository,
    IBuyersRepository: BuyersRepository,
    ISalesRepository: SalesRepository,
    IScheduleEventRepository: ScheduleEventRepository,
}
