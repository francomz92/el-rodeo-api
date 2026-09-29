from src.common.domain.repository import IRepository
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.repositories.gdpr_data_repository_port import (
    IMarketGDPRDataRepository,
)
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.repositories.sales_summary_report_query_port import (
    ISalesSummaryReportQuery,
)
from src.market.infrastructure.persistence.repositories.buyers import BuyersRepository
from src.market.infrastructure.persistence.repositories.gdpr_data_repository import (
    MarketGDPRDataRepository,
)
from src.market.infrastructure.persistence.repositories.sales import SalesRepository
from src.market.infrastructure.persistence.repositories.sales_summary_report_query import (
    SalesSummaryReportQuery,
)

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IBuyersRepository: BuyersRepository,
    ISalesRepository: SalesRepository,
    ISalesSummaryReportQuery: SalesSummaryReportQuery,
    IMarketGDPRDataRepository: MarketGDPRDataRepository,
}
