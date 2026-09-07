from src.billing.domain.repositories import IPaymentRepository, IPlanRepository, ISubscriptionRepository
from src.billing.infrastructure.persistence.repositories import PlanRepository
from src.billing.infrastructure.persistence.repositories._payment_repository import (
    PaymentRepository,
)
from src.billing.infrastructure.persistence.repositories._subscription_repository import (
    SubscriptionRepository,
)
from src.common.domain.repository import IRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IPaymentRepository: PaymentRepository,
    ISubscriptionRepository: SubscriptionRepository,
    IPlanRepository: PlanRepository,
}
