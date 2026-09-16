"""Repository registry for the reports bounded context."""

from src.common.domain.repository import IRepository
from src.reports.domain.repositories.reports_repository_port import (
    IReportsRepository,
)
from src.reports.infrastructure.persistence.repositories.reports_repository import (
    ReportsRepository,
)

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IReportsRepository: ReportsRepository,
}
