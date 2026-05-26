from src.auth.infrastructure.persistance.repositories.user_repository import IUserRepository, UserRepository
from src.cattle.infrastructure.persistance.repositories.animal_protocol_repository import (
    AnimalProtocolsRepository,
    IAnimalProtocolsRepository,
)
from src.cattle.infrastructure.persistance.repositories.animal_repository import AnimalRepository, IAnimalsRepository
from src.cattle.infrastructure.persistance.repositories.animal_type_repository import AnimalTypeRepository, IAnimalTypesRepository
from src.cattle.infrastructure.persistance.repositories.schedule_event_repository import IScheduleEventRepository, ScheduleEventRepository
from src.common.domain.repository import IRepository
from src.finance.infrastructure.persistance.repositories.animal_suppiles import AnimalSuppliesRepository, IAnimalSuppliesRepository
from src.finance.infrastructure.persistance.repositories.animal_supplie_types import ISupplyTypesRepository, SupplyTypesRepository
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
    IAnimalProtocolsRepository: AnimalProtocolsRepository,
}
