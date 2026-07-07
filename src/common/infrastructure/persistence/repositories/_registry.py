from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.infrastructure.persistence.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.auth.infrastructure.persistence.repositories.tenant_repository import (
    TenantRepository,
)
from src.auth.infrastructure.persistence.repositories.user_repository import IUserRepository, UserRepository
from src.billing.domain.repositories import IPaymentRepository, ISubscriptionRepository
from src.billing.infrastructure.persistence.repositories import (
    PaymentRepository,
    SubscriptionRepository,
)
from src.cattle.infrastructure.persistence.repositories.animal_protocol_repository import (
    AnimalProtocolsRepository,
    IAnimalProtocolsRepository,
)
from src.cattle.infrastructure.persistence.repositories.animal_repository import AnimalRepository, IAnimalsRepository
from src.cattle.infrastructure.persistence.repositories.animal_type_repository import AnimalTypeRepository, IAnimalTypesRepository
from src.cattle.infrastructure.persistence.repositories.schedule_event_repository import IScheduleEventRepository, ScheduleEventRepository
from src.common.domain.repository import IRepository
from src.finance.infrastructure.persistence.repositories.animal_supplies import AnimalSuppliesRepository, IAnimalSuppliesRepository
from src.finance.infrastructure.persistence.repositories.animal_supply_types import ISupplyTypesRepository, SupplyTypesRepository
from src.finance.infrastructure.persistence.repositories.purchases import IPurchasesRepository, PurchasesRepository
from src.market.infrastructure.persistence.repositories.buyers import BuyersRepository, IBuyersRepository
from src.market.infrastructure.persistence.repositories.sales import ISalesRepository, SalesRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IRefreshTokenRepository: RefreshTokenRepository,
    ITenantRepository: TenantRepository,
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
    IPaymentRepository: PaymentRepository,
    ISubscriptionRepository: SubscriptionRepository,
}
