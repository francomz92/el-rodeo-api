from src.common.domain.repository import IRepository
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.repositories.sales import ISalesRepository
from src.market.infrastructure.persistence.repositories.buyers import BuyersRepository
from src.market.infrastructure.persistence.repositories.sales import SalesRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IBuyersRepository: BuyersRepository,
    ISalesRepository: SalesRepository,
}
